# -*- coding: utf-8 -*-
# Standard Library
import contextlib
import random

# Cog Dependencies
import aiohttp
import discord
import lavalink

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, humanize_number, humanize_timedelta

_ = lambda s: s

MESSAGES = [
    "{flame.mention} <<<<<<<<<<<< Please dont bully the little pussy ass virgin",
    "{flame.mention} <<<<<<<<<<<< FUCK YOU BITCH",
    "{flame.mention} VIRGIN {flame.mention}",
    "{flame.mention} {flame.mention} {flame.mention}",
    "Pff asshole {flame.mention}",
]


class FlameIsDumb(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.session.detach()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.id == self.bot.user.id:
            return
        if message.channel.id not in [133251234164375552, 171665724262055936, 169868846759542785]:
            return
        guild = message.guild
        guild.get_member(208903205982044161)
        flame = guild.get_member(145519400223506432)
        content = ""
        if message.embeds:
            for embed in message.embeds:
                content += str(embed.to_dict()).lower()
        if message.content:
            content += message.content.lower()

        if message.author.id == 470684878107705344:
            if random.random() > 0.99:
                await message.channel.send(f"{message.author.mention} fuck you!", delete_after=10)
            return
        apiinsult = ""

        if (
            "208903205982044161" in content
            or "draper" in content
            or "flame" in content
            or "virgin" in content
            or "145519400223506432" in content
            or message.author.id in [470684878107705344, 145519400223506432]
        ):
            with contextlib.suppress(Exception):
                async with self.session.get("https://insult.mattbas.org/api/insult") as text:
                    apiinsult = await text.read()
                    apiinsult = apiinsult.decode()
            if not apiinsult:
                await message.channel.send(
                    random.choice(MESSAGES).format(flame=flame), delete_after=10
                )
            elif apiinsult:
                await message.channel.send(f"{flame.mention} {apiinsult}", delete_after=30)
