# -*- coding: utf-8 -*-
# Cog Relative Imports
from .main import FlameIsDumb


async def setup(bot):
    cog = FlameIsDumb(bot)
    bot.add_cog(cog)
