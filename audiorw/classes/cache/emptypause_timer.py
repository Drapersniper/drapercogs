# -*- coding: utf-8 -*-
# Standard Library
from typing import Dict, Optional

# Cog Dependencies
import discord

from redbot.core import Config
from redbot.core.bot import Red

# Cog Relative Imports
from ...utilities import constants


class EmptyPauseTimerManager:
    def __init__(self, bot: Red, config: Config, enable_cache: bool = True):
        self._config: Config = config
        self.bot = bot
        self.enable_cache = enable_cache
        self._cached: Dict[Optional[int], int] = {}

    async def get(self, guild: discord.Guild) -> int:
        ret: int
        gid: int = guild.id

        if self.enable_cache and gid in self._cached:
            ret = self._cached[gid]
        else:
            ret = await self._config.guild_from_id(gid).emptypause_timer()
            self._cached[gid] = ret

        return ret

    async def set(self, guild: discord.Guild, set_to: Optional[int]) -> None:
        gid: int = guild.id
        if set_to is not None:
            await self._config.guild_from_id(gid).emptypause_timer.set(set_to)
            self._cached[gid] = set_to
        else:
            await self._config.guild_from_id(gid).emptypause_timer.clear()
            self._cached[gid] = constants.DEFAULT_COG_SETTINGS_GUILD["emptypause_timer"]
