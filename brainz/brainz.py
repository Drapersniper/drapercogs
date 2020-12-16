import asyncio
import re
from typing import Optional

from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import humanize_list

import discord

from chatterbot import ChatBot, filters
from chatterbot.trainers import ChatterBotCorpusTrainer, ListTrainer, UbuntuCorpusTrainer


class Brainz(commands.Cog):
    """Adds neurons to [botname]."""

    def __init__(self, bot):
        self.bot = bot
        self.chat_bot: ChatBot = None
        self._list_trainer: ListTrainer = None
        self._corpus_trainer: ChatterBotCorpusTrainer = None
        self._ubuntu_trainer: UbuntuCorpusTrainer = None
        self.__database = cog_data_path(self) / "chatter.sqlite3"
        self._message_cache = []
        self._event = asyncio.Event()
        self.mention_regex: Optional[re.Pattern] = None
        self.config = Config.get_conf(self, identifier=208903205982044161, force_registration=True)

    @tasks.loop(seconds=15.0)
    async def learn(self):
        if self._message_cache and self._list_trainer:
            message_cache = self._message_cache.copy()
            self._message_cache.clear()
            self._list_trainer.traine(message_cache)
            del message_cache

    def cog_unload(self):
        self.learn.cancel()

    async def initialize(self):
        await self.bot.wait_until_red_ready()
        self.mention_regex = re.compile(rf"<@!?{self.bot.user.id}>")
        self._event.set()
        self.chat_bot = ChatBot(
            self.bot.user.name,
            storage_adapter="chatterbot.storage.SQLStorageAdapter",
            database_uri=f"sqlite:///{self.__database}",
            logic_adapters=[
                "chatterbot.logic.MathematicalEvaluation",
                "chatterbot.logic.TimeLogicAdapter",
                "chatterbot.logic.BestMatch",
            ],
            filters=[filters.get_recent_repeated_responses],
            preprocessors=[
                "chatterbot.preprocessors.clean_whitespace",
                "chatterbot.preprocessors.unescape_html",
                "chatterbot.preprocessors.convert_to_ascii",
            ],
        )
        self._list_trainer = ListTrainer(self.chat_bot)
        self._corpus_trainer = ChatterBotCorpusTrainer(self.chat_bot)
        self._ubuntu_trainer = UbuntuCorpusTrainer(self.chat_bot)
        self.learn.start()

    @commands.Cog.listener()
    async def on_message_without_command(self, message: discord.Message):
        if message.author.bot:
            return
        self._message_cache.append(message.clean_content)

        if (not self._event.is_set()) or self.mention_regex is None:
            return
        if not self.mention_regex.search(message.content):
            return

        guild = message.guild
        channel = message.channel
        author = message.author

        if guild and (
            not channel.permissions_for(guild.me).send_messages
            or (await self.bot.cog_disabled_in_guild(self, guild))
            or not (await self.bot.ignored_channel_or_guild(message))
        ):
            return
        if not (await self.bot.allowed_by_whitelist_blacklist(author)):
            return

        if guild:
            perms = message.channel.permissions_for(guild.me)
        else:
            perms = message.channel.permissions_for(self.bot.user)

        if perms.send_messages:
            await message.channel.send(self.chat_bot.get_response(message.clean_content))

    @commands.group(name="feed")
    @commands.is_owner()
    async def command_feed(self, ctx: commands.Context):
        """Training commands."""

    @command_feed.command(name="ubuntu")
    async def command_feed_ubuntu(self, ctx: commands.Context, *, language: str.lower):
        """Train [botname] with the community Ubuntu dataset."""
        async with ctx.typing():
            self._ubuntu_trainer.train()
        await ctx.send(
            f"{ctx.author.mention} I've have learnt a lot about this thing you call 'Internet'."
        )

    @command_feed.command(name="language")
    async def command_feed_language(self, ctx: commands.Context, *, language: str.lower):
        """Train [botname] in the specified languages."""
        supported_language = {
            "bengali",
            "chinese",
            "english",
            "french",
            "german",
            "hebrew",
            "hindi",
            "indonesian",
            "italian",
            "japanese",
            "korean",
            "marathi",
            "oriya",
            "persian",
            "portuguese",
            "russian",
            "spanish",
            "swedish",
            "telugu",
            "thai",
            "traditionalchinese",
            "turkish",
        }
        if language not in supported_language:
            return await ctx.send(
                f"`{language}` is not a supported language, please use one of the following\n\n"
                f"{humanize_list(supported_language, style='or')}"
            )
        await ctx.send(f"I'm being trained on {language.title()}")
        async with ctx.typing():
            self._corpus_trainer.train(f"chatterbot.corpus.{language}")

        await ctx.send(f"{ctx.author.mention} I've have learnt a lot about {language.title()}.")

    @command_feed.command(name="local")
    async def command_feed_local(
        self, ctx: commands.Context, *, channel: Optional[discord.TextChannel] = None
    ):
        """Train [botname] in the current server or specified channel.

        THIS MAY TAKE A VERY LONG TIME.
        """
        async with ctx.typing():
            if channel:
                perms = channel.permissions_for(ctx.me)
                if perms.read_message_history and perms.read_messages:
                    messages = (
                        await channel.history(limit=None)
                        .filter(lambda m: not m.author.bot)
                        .flatten()
                    )
                    self._message_cache.extend([m.clean_content for m in messages])
                else:
                    return await ctx.send(
                        "I need `Read Messages` and `Read Message History` in "
                        f"{channel.mention} to learn from it"
                    )
            else:
                if ctx.guild:
                    for channel in ctx.guild.text_channels:
                        perms = channel.permissions_for(ctx.me)
                        if perms.read_message_history and perms.read_messages:
                            messages = (
                                await channel.history(limit=None)
                                .filter(lambda m: not m.author.bot)
                                .flatten()
                            )
                            self._message_cache.extend([m.clean_content for m in messages])
                else:
                    messages = (
                        await channel.history(limit=None)
                        .filter(lambda m: not m.author.bot)
                        .flatten()
                    )
                    self._message_cache.extend([m.clean_content for m in messages])
        if channel:
            await ctx.send(f"{ctx.author.mention} I've have learnt a lot about {channel.mention}")
        elif ctx.guild:
            await ctx.send(f"{ctx.author.mention} I've have learnt a lot about {ctx.guild.name}")
        else:
            await ctx.send(f"{ctx.author.mention} I've have learnt a lot about our conversations.")
