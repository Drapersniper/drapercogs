from .antibot import AntiBot


async def setup(bot):
    cog = AntiBot(bot)
    await cog.initialize()
    bot.add_cog()
