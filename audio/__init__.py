# -*- coding: utf-8 -*-
# Standard Library
import asyncio
import sys

# Cog Dependencies
from redbot.core.bot import Red

# Cog Relative Imports
from .core import Audio

async def setup(bot: Red):
    cog = Audio(bot)
    bot.add_cog(cog)
    cog.start_up_task()
