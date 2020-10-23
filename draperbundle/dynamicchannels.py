# -*- coding: utf-8 -*-
import asyncio
import contextlib
import json
import logging
from collections import defaultdict
from datetime import timedelta
from operator import itemgetter
from typing import Union, Optional, Dict

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.antispam import AntiSpam
from redbot.core.utils.chat_formatting import box

from .config_holder import ConfigHolder

log = logging.getLogger("red.drapercogs.dynamic_channels")


class DynamicChannels(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = ConfigHolder.DynamicChannels
        self.task = self.bot.loop.create_task(self.clean_up_dynamic_channels())
        self.antispam: Dict[int, Dict[int, AntiSpam]] = {}
        self.config_cache = defaultdict(dict)

    def cog_unload(self):
        if self.task:
            self.task.cancel()

    @commands.admin_or_permissions()
    @commands.guild_only()
    @commands.bot_has_permissions(manage_channels=True, manage_roles=True)
    @commands.group(name="dynamicset")
    async def _button(self, ctx: commands.Context):
        """Configure dynamic voice channels."""

    @_button.command(name="blacklistadd")
    async def _button_blacklist(self, ctx: commands.Context, *users: discord.Member):
        """Disallow a user from using the custom channels."""

        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            blacklisted_users = blacklist["blacklist"]
            blacklisted_users.expand([u.id for u in users])
            blacklist["blacklist"] = list(set(blacklisted_users))

        self.config_cache[ctx.guild.id]["blacklist"] = await self.config.guild(
            ctx.guild
        ).blacklist()
        await ctx.tick()

    @_button.command(name="blacklistremove")
    async def _button_blacklist(self, ctx: commands.Context, *users: discord.Member):
        """Remove users from the blacklist a user from using the custom channels."""

        async with self.config.guild(ctx.guild).blacklist() as blacklist:
            blacklisted_users = blacklist["blacklist"]
            blacklisted_users = [
                u for u in blacklisted_users if u not in [m.id for m in users]
            ]
            blacklist["blacklist"] = list(set(blacklisted_users))

        self.config_cache[ctx.guild.id]["blacklist"] = await self.config.guild(
            ctx.guild
        ).blacklist()
        await ctx.tick()

    @_button.command(name="add")
    async def _button_add(
        self,
        ctx: commands.Context,
        category_id: str,
        size: Optional[int] = 0,
        *,
        room_name: str,
    ):
        """Whitelist a category to have multiple types of Dynamic voice channels."""
        valid_categories = {
            str(category.id): category.name
            for category in ctx.guild.categories
            if category
        }

        if valid_categories and category_id not in valid_categories:
            await ctx.send(
                f"ERROR: {category_id} is not a valid category ID for {ctx.guild.name}, "
                f"these are the valid ones: "
            )
            await ctx.send(box(json.dumps(valid_categories, indent=2), lang="json"))
            return
        elif not valid_categories:
            await ctx.send(f"ERROR: No valid categories in {ctx.guild.name}")
            return

        category = next(
            (c for c in ctx.guild.categories if c.id == int(category_id)), None
        )
        await ctx.guild.create_voice_channel(
            user_limit=size,
            name=room_name.format(number=1),
            reason=f"We need extra rooms in {category.name}",
            category=category,
            bitrate=ctx.guild.bitrate_limit,
        )
        guild_data = ConfigHolder.DynamicChannels.guild(ctx.guild)
        async with guild_data.dynamic_channels() as whitelist:
            whitelist.update({category_id: [(room_name, size)]})
            await ctx.send(
                f"Added {category_id} to the whitelist\n"
                f"Rooms will be called {room_name} and have a size of {size}"
            )
        self.config_cache[ctx.guild.id]["dynamic_channels"] = await self.config.guild(
            ctx.guild
        ).dynamic_channels()

    @_button.command(name="append")
    async def multiple_dynamic_channel_whistelist_append(
        self, ctx, category_id: str, size: Optional[int] = 0, *, room_name: str
    ):
        """Whitelist a category to have multiple types of Dynamic voice channels."""
        valid_categories = {
            f"{category.id}": category.name
            for category in ctx.guild.categories
            if category
        }
        whitelisted_cat = await ConfigHolder.DynamicChannels.guild(
            ctx.guild
        ).dynamic_channels.get_raw()
        if valid_categories and category_id not in valid_categories:
            await ctx.send(
                f"ERROR: {category_id} is not a valid category ID for "
                f"{ctx.guild.name}, these are the valid ones: "
            )
            await ctx.send(box(json.dumps(valid_categories, indent=2), lang="json"))
            return
        elif not valid_categories:
            await ctx.send(f"ERROR: No valid categories in {ctx.guild.name}")
            return
        elif category_id not in whitelisted_cat:
            await ctx.send(
                f"ERROR: Category {category_id} is not been whitelisted as a "
                f"special category {ctx.guild.name}, use `{self._button_add.qualified_name}`"
            )
            return

        category = next(
            (c for c in ctx.guild.categories if c.id == int(category_id)), None
        )
        await ctx.guild.create_voice_channel(
            user_limit=size,
            name=room_name.format(number=1),
            reason=f"We need extra rooms in {category.name}",
            category=category,
            bitrate=ctx.guild.bitrate_limit,
        )

        guild_data = ConfigHolder.DynamicChannels.guild(ctx.guild)
        async with guild_data.dynamic_channels() as whitelist:
            whitelist[category_id].append((room_name, size))
            await ctx.send(
                f"Added {category_id} to the whitelist\nRooms will be called "
                f"{room_name} and have a size of {size}"
            )
        self.config_cache[ctx.guild.id]["dynamic_channels"] = await self.config.guild(
            ctx.guild
        ).dynamic_channels()

    @_button.command(name="remove")
    async def multiple_dynamic_channel_whistelist_delete(
        self, ctx: commands.Context, category_id: str
    ):
        """Remove the special category from Dynamic voice channels whitelist"""
        guild_data = ConfigHolder.DynamicChannels.guild(ctx.guild)
        async with guild_data.dynamic_channels() as whitelist:
            if category_id in whitelist:
                del whitelist[f"{category_id}"]
                await ctx.send(f"Removed {category_id} from the whitelist")
            else:
                await ctx.send(f"Error: {category_id} is not a whitelisted category")
        self.config_cache[ctx.guild.id]["dynamic_channels"] = await self.config.guild(
            ctx.guild
        ).dynamic_channels()

    @commands.Cog.listener()
    async def on_guild_channel_delete(
        self,
        channel: Union[
            discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel
        ],
    ):
        has_perm = channel.guild.me.guild_permissions.manage_channels
        if not has_perm:
            return
        if "dynamic_channels" not in self.config_cache[channel.guild.id]:
            self.config_cache[channel.guild.id][
                "dynamic_channels"
            ] = await self.config.guild(channel.guild).dynamic_channels()
        if (
            isinstance(channel, discord.VoiceChannel)
            and channel.category
            and f"{channel.category.id}"
            in (self.config_cache[channel.guild.id]["dynamic_channels"])
        ):
            log.debug(
                f"Dynamic Channel ({channel.id}) has been deleted checking if it exist in database"
            )
            channel_group = self.config.guild(channel.guild)
            async with channel_group.user_created_voice_channels() as channel_data:
                if f"{channel.id}" in channel_data:
                    log.debug(
                        f"Dynamic Channel ({channel.id}) has been deleted from database"
                    )
                    del channel_data[f"{channel.id}"]

    @commands.Cog.listener()
    async def on_guild_channel_create(
        self,
        channel: Union[
            discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel
        ],
    ):
        has_perm = channel.guild.me.guild_permissions.manage_channels
        if not has_perm:
            return
        if "dynamic_channels" not in self.config_cache[channel.guild.id]:
            self.config_cache[channel.guild.id][
                "dynamic_channels"
            ] = await self.config.guild(channel.guild).dynamic_channels()
        if (
            isinstance(channel, discord.VoiceChannel)
            and channel.category
            and f"{channel.category.id}"
            in (self.config_cache[channel.guild.id]["dynamic_channels"])
        ):
            log.debug(
                f"Dynamic Channel ({channel.id}) has been created adding to database"
            )
            channel_group = self.config.guild(channel.guild)
            async with channel_group.user_created_voice_channels() as channel_data:
                channel_data.update({channel.id: channel.name})

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        guild = member.guild
        has_perm = guild.me.guild_permissions.manage_channels
        if not has_perm:
            return
        if member.bot:
            return
        if "dynamic_channels" not in self.config_cache[member.guild.id]:
            self.config_cache[member.guild.id][
                "dynamic_channels"
            ] = await self.config.guild(member.guild).dynamic_channels()
        if not self.config_cache[member.guild.id]["dynamic_channels"]:
            return
        if "blacklist" not in self.config_cache[member.guild.id]:
            self.config_cache[member.guild.id]["blacklist"] = await self.config.guild(
                member.guild
            ).blacklist()
        if member.id in self.config_cache[member.guild.id]["blacklist"]:
            return
        if guild.id not in self.antispam:
            self.antispam[guild.id] = {}

        if member.id not in self.antispam[guild.id]:
            self.antispam[guild.id][member.id] = AntiSpam([(timedelta(seconds=60), 2)])

        delete = {}
        whitelist = await self.config.guild(member.guild).dynamic_channels.get_raw()
        guild_channels = member.guild.by_category()
        for category, _ in guild_channels:
            if (
                after
                and after.channel
                and before.channel != after.channel
                and after.channel.category
                and after.channel.category == category
                and f"{after.channel.category.id}" in whitelist
            ):
                voice_channels = category.voice_channels
                voice_channels_empty = [
                    channel
                    for channel in voice_channels
                    if sum(1 for _ in channel.members) < 1
                ]
                category_config = whitelist[f"{after.channel.category.id}"]
                for room_name, room_size in category_config:
                    keyword = room_name.split(" -")[0]
                    keyword = f"{keyword} -"
                    type_room = [
                        (channel.name, channel.position, channel)
                        for channel in voice_channels_empty
                        if keyword in channel.name
                    ]
                    channel_count = [
                        channel for channel in voice_channels if keyword in channel.name
                    ]

                    type_room.sort(key=itemgetter(1))

                    if room_size < 2:
                        room_size = 0

                    if not type_room and not self.antispam[guild.id][member.id].spammy:
                        self.antispam[guild.id][member.id].stamp()
                        created_channel = await member.guild.create_voice_channel(
                            user_limit=room_size,
                            name=room_name.format(number=len(channel_count) + 1),
                            reason=f"We need extra rooms in {category.name}",
                            category=category,
                            bitrate=member.guild.bitrate_limit,
                        )
                        guild_group = self.config.guild(member.guild)
                        async with guild_group.user_created_voice_channels() as user_voice:
                            user_voice.update({created_channel.id: created_channel.id})

                    elif len(type_room) > 1:
                        for channel_name, position, channel in type_room:
                            if channel_name != room_name.format(number=1):
                                delete.update({channel.id: (channel, position)})
            elif (
                before
                and before.channel
                and before.channel != after.channel
                and before.channel.category
                and before.channel.category == category
                and f"{before.channel.category.id}" in whitelist
            ):
                category = before.channel.category
                voice_channels = category.voice_channels
                voice_channels_empty = [
                    channel
                    for channel in voice_channels
                    if sum(1 for _ in channel.members) < 1
                ]
                category_config = whitelist[f"{before.channel.category.id}"]
                for room_name, room_size in category_config:
                    keyword = room_name.split(" -")[0]
                    keyword = f"{keyword} -"
                    type_room = [
                        (channel.name, channel.position, channel)
                        for channel in voice_channels_empty
                        if keyword in channel.name
                    ]
                    channel_count = [
                        channel for channel in voice_channels if keyword in channel.name
                    ]
                    type_room.sort(key=itemgetter(1))
                    if room_size < 3:
                        room_size = 0

                    if not type_room and not self.antispam[guild.id][member.id].spammy:
                        self.antispam[guild.id][member.id].stamp()
                        log.debug(f"We need extra dynamic rooms in {category.name}")
                        created_channel = await member.guild.create_voice_channel(
                            user_limit=room_size,
                            name=room_name.format(number=len(channel_count) + 1),
                            reason=f"We need extra rooms in {category.name}",
                            category=category,
                            bitrate=member.guild.bitrate_limit,
                        )
                        log.debug(
                            f"New dynamic channel has been created: {created_channel.name}"
                        )
                        guild_group = self.config.guild(member.guild)
                        async with guild_group.user_created_voice_channels() as user_voice:
                            user_voice.update({created_channel.id: created_channel.id})

                    elif len(type_room) > 1:
                        for channel_name, position, channel in type_room:
                            if channel_name != room_name.format(number=1):
                                delete.update({channel.id: (channel, position)})
        if delete and len(delete) >= 1:
            log.debug(f"Some dynamic channels need to be deleted")
            guild_group = self.config.guild(member.guild)
            async with guild_group.user_created_voice_channels() as user_voice:
                for _, channel_data in delete.items():
                    channel, _ = channel_data
                    log.debug(f"{channel.name} will be deleted")
                    with contextlib.suppress(discord.HTTPException):
                        await channel.delete(
                            reason="Deleting channel due to it being empty"
                        )
                        log.debug(f"{channel.name} has been deleted")
                    if f"{channel.id}" in user_voice:
                        del user_voice[f"{channel.id}"]

    async def clean_up_dynamic_channels(self):
        with contextlib.suppress(asyncio.CancelledError):
            try:
                await self.bot.wait_until_ready()
                guilds = self.bot.guilds
                while guilds and True:
                    guilds = self.bot.guilds
                    for guild in guilds:
                        has_perm = guild.me.guild_permissions.manage_channels
                        keep_id = {}
                        data = await self.config.guild(
                            guild
                        ).user_created_voice_channels()
                        for channel_id in list(data.items()):
                            channel = guild.get_channel(channel_id)
                            if channel:
                                if sum(1 for _ in channel.members) < 1:
                                    if has_perm:
                                        await asyncio.sleep(5)
                                        await channel.delete(
                                            reason=(
                                                "User created channel was "
                                                "empty during cleanup cycle"
                                            )
                                        )
                                else:
                                    keep_id.update({channel_id: channel_id})
                        await self.config.guild(guild).user_created_voice_channels.set(
                            keep_id
                        )
                    await asyncio.sleep(60)
            except Exception as e:
                log.exception("Error on channel cleanup", exc_info=e)
