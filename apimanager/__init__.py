from redbot.core.bot import Red

from .main import APIManager


def setup(bot: Red):
    cog = APIManager(bot)
    bot.add_cog(cog=cog)
