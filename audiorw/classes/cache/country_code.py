# -*- coding: utf-8 -*-
# Standard Library
from typing import Dict, Optional

# Cog Dependencies
import discord

from redbot.core import Config, commands
from redbot.core.bot import Red

# Cog Relative Imports
from ...utilities import constants


class CountryCodeManager:
    def __init__(self, bot: Red, config: Config, enable_cache: bool = True):
        self._config: Config = config
        self.bot = bot
        self.enable_cache = enable_cache
        self._cached_user: Dict[int, Optional[str]] = {}
        self._cached_guilds: Dict[int, str] = {}

    async def get_user(self, user: discord.Member) -> Optional[str]:
        ret: Optional[str]
        uid: int = user.id
        if self.enable_cache and uid in self._cached_user:
            ret = self._cached_user[uid]
        else:
            ret = await self._config.user_from_id(uid).country_code()
            self._cached_user[uid] = ret

        return ret

    async def set_user(self, user: discord.Member, set_to: Optional[str]) -> None:
        uid: int = user.id
        if set_to is not None:
            await self._config.cache_level.set(set_to)
            self._cached_user[uid] = set_to
        else:
            await self._config.cache_level.clear()
            self._cached_user[uid] = constants.DEFAULT_COG_SETTINGS_USER["country_code"]

    async def get_guild(self, guild: discord.Guild) -> str:
        ret: str

        gid: int = guild.id

        if self.enable_cache and gid in self._cached_guilds:
            ret = self._cached_guilds[gid]
        else:
            ret = await self._config.guild_from_id(gid).country_code()
            self._cached_guilds[gid] = ret

        return ret

    async def set_guild(self, guild: discord.Guild, set_to: Optional[str]) -> None:
        gid: int = guild.id
        if set_to:
            await self._config.guild_from_id(gid).country_code.set(set_to)
            self._cached_guilds[gid] = set_to
        else:
            await self._config.guild_from_id(gid).ignored.clear()
            self._cached_user[gid] = constants.DEFAULT_COG_SETTINGS_GUILD["country_code"]

    async def get_country_code(
        self,
        context: commands.Context,
        guild: Optional[discord.guild] = None,
        user: Optional[discord.Member] = None,
    ) -> str:
        return await self.get_user(user or context.author) or await self.get_guild(
            guild or context.guild
        )
