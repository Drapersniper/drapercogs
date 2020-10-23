# -*- coding: utf-8 -*-
import asyncio
import contextlib
import json
import logging

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify

from .config_holder import ConfigHolder
from .utilities import get_member_activity, get_supported_platforms

__updated__ = "17-04-2019"
logger = logging.getLogger("red.drapercogs.publisher_manager")


class PublisherManager(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = ConfigHolder.PublisherManager
        self.task = self.bot.loop.create_task(self.update_game_database())

    def cog_unload(self):
        if self.task:
            self.task.cancel()

    @commands.group(enabled=True, case_insensitive=True)
    async def service(self, ctx: commands.Context):
        """Add,Remove,Show services"""

    @commands.is_owner()
    @service.command(name="add", aliases=["+"])
    async def service_add(self, ctx: commands.Context, identifier: str, *, name: str):
        """Add a service to the list of supported services"""
        new_service = dict(name=name, identifier=identifier)
        new_service = {new_service["identifier"]: new_service}

        service_group = self.config
        async with service_group.services() as services:
            services.update(new_service)
        await ctx.tick()

    @commands.is_owner()
    @service.command(name="remove", aliases=["-", "delete"])
    async def service_remove(
        self, ctx: commands.Context, *, message: str
    ):  # @UnusedVariable
        """Remove a service from the list of supported services"""
        service_group = self.config
        async with service_group.services() as services:
            services.pop(message)
        await ctx.tick()

    @service.command(name="show")
    @commands.guild_only()
    async def service_show(self, ctx: commands.Context):
        """Show all services in the list of supported services"""
        platforms = await get_supported_platforms()
        embed = discord.Embed(title="Supported Platforms are:")
        for command, name in platforms:
            embed.add_field(name=name, value=f"Command: {command}", inline=False)
        await ctx.send(embed=embed)

    @commands.is_owner()
    @service.command(name="playing", enabled=True)
    async def service_playing(self, ctx: commands.Context):
        """Shows how many games needs to be parsed"""
        await self.update_game_database(manual=True)
        config_data = await self.config.publisher.get_raw()
        existing_data = [key for key, value in config_data.items() if value is None]
        await ctx.send(f"{len(existing_data)} games need to be parsed")
        json_data = json.dumps(config_data, indent=2)
        pages = pagify(json_data)
        for page in pages:
            await ctx.send(page)
        await ctx.tick()

    @commands.is_owner()
    @service.group(name="parse")
    async def _parse(self, ctx: commands.Context):
        """Parses game database"""

    @_parse.command(name="completed")
    async def _parse_completed(self, ctx: commands.Context, value: str):
        """Reparses completed with the following value

        Accepts a Service, True, False, None, all
        """
        checker = value.lower()

        if checker == "none":
            checker = None
        elif checker == "true":
            checker = True
        elif checker == "false":
            checker = False

        config_data = await self.config.publisher()
        if checker == "all":
            existing_data = [
                key
                for key, value in config_data.items()
                if value not in [None, True, False]
            ]
        else:
            existing_data = [
                key for key, value in config_data.items() if value == checker
            ]
        await self.parse_playing(ctx, existing_data)

    @_parse.command(name="game")
    async def _parse_game(self, ctx: commands.Context, *, game: str):
        """Parses a specific game"""
        checker = game.lower()

        config_data = await self.config.publisher()
        existing_data = [
            key for key, _ in config_data.items() if checker in key.lower()
        ]
        if not existing_data:
            return await ctx.send("I've never seen anyone playing this game")
        await self.parse_playing(ctx, existing_data)

    @_parse.command(name="incomplete")
    async def incomplete_parse_game(self, ctx: commands.Context):
        """Parses games that haven't been parsed"""
        config_data = await self.config.publisher()
        existing_data = [key for key, value in config_data.items() if value is None]
        await self.parse_playing(ctx, existing_data)

    async def parse_playing(self, ctx, existing_data):
        """Parsed game database"""

        async def services_parser(
            game, author: discord.User, sender
        ):  # @UnusedVariable
            def check(m):
                return m.author == author

            async def smart_prompt(prompt_data: dict, platforms: dict):
                while True:
                    embed = discord.Embed(
                        title=f"Pick a number that matches the service you want to add to {game}"
                    )
                    for key, value in prompt_data.items():
                        embed.add_field(name=value, value=key)
                    await sender(embed=embed)

                    valid_keys = map(str, list(prompt_data.keys())[:-2])
                    msg = await self.bot.wait_for("message", check=check)
                    if msg and msg.content.lower() in valid_keys:
                        key = msg.content
                        name = prompt_data.get(msg.content, "")
                        command = next(
                            (
                                command_toget
                                for command_toget, name_toget in platforms
                                if name_toget == name
                            ),
                            None,
                        )
                        if name and command:
                            return command
                    elif msg and prompt_data.get(msg.content, "").lower() == "none":
                        return False
                    elif msg and prompt_data.get(msg.content, "").lower() == "delete":
                        return "delete"
                    else:
                        key = 999

            platforms = await get_supported_platforms()
            platform_prompt = [name for _, name in platforms]
            platform_prompt = {
                str(counter): name for counter, name in enumerate(platform_prompt)
            }
            platform_prompt.update({str(len(platform_prompt)): "none"})
            platform_prompt.update({str(len(platform_prompt)): "delete"})
            return await smart_prompt(platform_prompt, platforms)

        if existing_data:
            service_group = self.config
            async with service_group.publisher() as publisher_data:
                for game in existing_data:
                    await asyncio.sleep(0)
                    publisher = await services_parser(game, ctx.author, ctx.send)
                    if publisher != "delete":
                        publisher_data.update({game: publisher})
                    else:
                        if game in publisher_data:
                            del publisher_data[game]
        await ctx.send("Done")

    async def update_game_database(self, manual=False):
        with contextlib.suppress(asyncio.CancelledError):
            timer = 900
            guilds = self.bot.guilds
            while True and guilds:
                guilds = self.bot.guilds
                for guild in guilds:
                    members = guild.members
                    config_data = await self.config.publisher.get_raw()
                    new_data = []
                    for member in members:
                        await asyncio.sleep(0.2)
                        activity = get_member_activity(member, database=True)
                        if (
                            not member.bot
                            and activity
                            and activity not in config_data
                            and activity not in new_data
                        ):
                            new_data.append(activity)
                    if new_data:
                        service_group = self.config
                        async with service_group.publisher() as publisher:
                            for game in new_data:
                                publisher.update({game: None})
                if manual:
                    break
                await asyncio.sleep(timer)
