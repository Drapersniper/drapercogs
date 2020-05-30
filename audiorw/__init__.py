# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Cog Relative Imports
from .core import Audio

if TYPE_CHECKING:
    from redbot.core.bot import Red


def setup(bot: Red) -> None:
    cog = Audio(bot)
    bot.add_cog(cog)
