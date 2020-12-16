import asyncio

from .brainz import Brainz


def setup(bot):
    cog = Brainz(bot)
    bot.add_cog(cog)
    asyncio.create_task(cog.initialize())
