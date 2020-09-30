# Cog Dependencies
from redbot.core import commands

# Cog Relative Imports
from .main import Music


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
