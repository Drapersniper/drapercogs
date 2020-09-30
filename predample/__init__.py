# -*- coding: utf-8 -*-
# Cog Relative Imports
from .main import ErrorCounter


async def setup(bot):
    cog = ErrorCounter(bot)
    bot.add_cog(cog)
