from redbot.core.bot import Red

from .main import APIAccess


def setup(bot: Red):
    cog = APIAccess(bot)
    bot.add_cog(cog=cog)
