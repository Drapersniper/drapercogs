# -*- coding: utf-8 -*-
# Standard Library
from collections import Counter

# Cog Dependencies
import discord
import wavelink

from redbot.core import Config, commands as red_commands
from redbot.core.bot import Red

# Cog Relative Imports
from ..classes.meta import CompositeMetaClass
from ..classes.playlists import PlaylistScope
from ..utilities import constants
from . import commands, events, tasks, utilities


class Audio(
    commands.Commands,
    events.Events,
    tasks.Tasks,
    utilities.Utilities,
    red_commands.Cog,
    metaclass=CompositeMetaClass,
):
    """Play audio through voice channels."""

    def __init__(self, bot: Red) -> None:
        super().__init__()
        self.bot = bot
        self.config = Config.get_conf(self, 2711759130, force_registration=True)

        self.api_interface = None
        self.player_manager = None
        self.playlist_api = None
        self.local_folder_current_path = None
        self.db_conn = None

        self._error_counter = Counter()
        self._error_timer = {}
        self._disconnected_players = {}
        self._daily_playlist_cache = {}
        self._daily_global_playlist_cache = {}
        self._persist_queue_cache = {}
        self._dj_status_cache = {}
        self._dj_role_cache = {}
        self.play_lock = {}

        self.lavalink_connect_task = None
        self.player_automated_timer_task = None
        self.cog_init_task = None
        self.cog_cleaned_up = False
        self.lavalink_connection_aborted = False
        self.permission_cache = discord.Permissions(**constants.DEFAULT_COG_SETTINGS_PERMISSIONS)

        self.config.init_custom("EQUALIZER", 1)
        self.config.init_custom(PlaylistScope.GLOBAL.value, 1)
        self.config.init_custom(PlaylistScope.GUILD.value, 2)
        self.config.init_custom(PlaylistScope.USER.value, 2)
        self.config.register_custom("EQUALIZER", **constants.DEFAULT_COG_SETTINGS_EQUALIZER)
        self.config.register_custom(
            PlaylistScope.GLOBAL.value, **constants.DEFAULT_COG_SETTINGS_PLAYLISTS
        )
        self.config.register_custom(
            PlaylistScope.GUILD.value, **constants.DEFAULT_COG_SETTINGS_PLAYLISTS
        )
        self.config.register_custom(
            PlaylistScope.USER.value, **constants.DEFAULT_COG_SETTINGS_PLAYLISTS
        )
        self.config.register_guild(**constants.DEFAULT_COG_SETTINGS_GUILD)
        self.config.register_global(**constants.DEFAULT_COG_SETTINGS_GLOBAL)
        self.config.register_user(**constants.DEFAULT_COG_SETTINGS_USER)
        if bot.wavelink is None:
            bot.wavelink = wavelink.Client(bot=bot)
        bot.loop.create_task(self.start_nodes())

    async def start_nodes(self) -> None:
        """Connect and intiate nodes."""
        await self.bot.wait_until_ready()

        if self.bot.wavelink.nodes:
            previous = self.bot.wavelink.nodes.copy()

            for node in previous.values():
                await node.destroy()

        nodes = {
            "LOCAL": {
                "host": "localhost",
                "port": 2333,
                "rest_uri": "http://localhost:2333",
                "password": "youshallnotpass",
                "identifier": "LOCAL",
                "region": "us_central",
            }
        }

        for n in nodes.values():
            node = await self.bot.wavelink.initiate_node(**n)
            node.set_hook(self.node_event_hook)

    async def node_event_hook(self, event: wavelink.WavelinkEvent) -> None:
        """Node event hook."""
        if isinstance(event, (wavelink.TrackStuck, wavelink.TrackException, wavelink.TrackEnd)):
            await event.player.do_next()
