# -*- coding: utf-8 -*-
# Standard Library
from pathlib import Path
from typing import Dict, Optional

# Cog Dependencies
from redbot.core import Config
from redbot.core.bot import Red

# Cog Relative Imports
from ...utilities import constants


class LocalPathManager:
    def __init__(self, bot: Red, config: Config, enable_cache: bool = True):
        self._config: Config = config
        self.bot = bot
        self.enable_cache = enable_cache
        self._cached: Dict[Optional[int], str] = {}

    async def get(self) -> Path:
        ret: str
        gid = None

        if self.enable_cache and gid in self._cached:
            ret = self._cached[gid]
        else:
            ret = await self._config.localpath()
            self._cached[gid] = ret

        return Path(ret).absolute()

    async def set(self, set_to: Optional[Path]) -> None:
        gid = None
        if set_to is not None:
            await self._config.localpath.set(set_to)
            self._cached[gid] = str(set_to.absolute())
        else:
            await self._config.localpath.clear()
            self._cached[gid] = constants.DEFAULT_COG_SETTINGS_GLOBAL["localpath"]
