from .main import PokeGram


async def setup(bot):
    cog = PokeGram(bot)
    bot.add_cog(cog)
    await cog.initialize()
