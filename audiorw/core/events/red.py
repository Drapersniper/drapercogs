# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
import logging

from typing import Mapping

# Cog Dependencies
from redbot.core import commands

# Cog Relative Imports
from ...abc import MixinMeta
from ...classes.meta import CompositeMetaClass

__log__ = logging.getLogger("red.cogs.Audio.cog.Events.red")


class RedEvents(MixinMeta, metaclass=CompositeMetaClass):
    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ) -> None:
        pass
