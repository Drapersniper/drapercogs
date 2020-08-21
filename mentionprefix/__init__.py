# -*- coding: utf-8 -*-
# Cog Relative Imports
from .mentionprefix import MentionPrefix


async def setup(bot):
    cog = MentionPrefix(bot)
    bot.add_cog(cog)
    await cog.initialize()
