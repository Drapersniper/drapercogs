# Cog Dependencies
from redbot.core.bot import Red

# Cog Relative Imports
from .core import Audio


def setup(bot: Red):
    cog = Audio(bot)
    bot.add_cog(cog)
    cog.start_up_task()
