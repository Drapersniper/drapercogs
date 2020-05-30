# -*- coding: utf-8 -*-
# Standard Library
from typing import Dict, Optional

# Cog Dependencies
import discord

from redbot.core import Config
from redbot.core.bot import Red

# Cog Relative Imports
from ...utilities import constants


class DailyPlaylistManager:
    def __init__(self, bot: Red, config: Config, enable_cache: bool = True):
        self._config: Config = config
        self.bot = bot
        self.enable_cache = enable_cache
        self._cached: Dict[Optional[int], bool] = {}

    async def get(self, guild: discord.Guild) -> bool:
        ret: bool
        gid: int = guild.id

        if self.enable_cache and gid in self._cached:
            ret = self._cached[gid]
        else:
            ret = await self._config.guild_from_id(gid).daily_playlists()
            self._cached[gid] = ret

        return ret

    async def set(self, guild: discord.Guild, set_to: Optional[bool]) -> None:
        gid: int = guild.id
        if set_to is not None:
            await self._config.guild_from_id(gid).daily_playlists.set(set_to)
            self._cached[gid] = set_to
        else:
            await self._config.guild_from_id(gid).daily_playlists.clear()
            self._cached[gid] = constants.DEFAULT_COG_SETTINGS_GUILD["daily_playlists"]
