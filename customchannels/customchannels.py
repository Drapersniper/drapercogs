import asyncio
import contextlib
import json
import logging
from typing import Union

import discord

from redbot.core import commands, checks
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from draper_lib.config_holder import ConfigHolder

admin_permissions = discord.PermissionOverwrite(
    speak=True,
    connect=True,
    mute_members=True,
    deafen_members=True,
    move_members=True,
    priority_speaker=True,
    manage_channels=True,
    use_voice_activation=True,
    read_messages=True,
)

muted_permissions = discord.PermissionOverwrite(
    speak=False,
    connect=False,
    mute_members=False,
    deafen_members=False,
    move_members=False,
    priority_speaker=False,
    manage_channels=False,
    use_voice_activation=False,
    read_messages=False,
)

creator_permissions = discord.PermissionOverwrite(
    speak=True,
    connect=True,
    mute_members=True,
    priority_speaker=True,
    manage_channels=True,
    use_voice_activation=True,
    read_messages=True,
)

default_permission = discord.PermissionOverwrite(
    speak=True, connect=True, use_voice_activation=True, read_messages=True
)

logger = logging.getLogger("red.drapercogs.button_channel")


class CustomChannels(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.config = ConfigHolder.CustomChannels
        self.task = self.bot.loop.create_task(self.clean_up_custom_channels())

    def cog_unload(self):
        if self.task:
            self.task.cancel()

    @checks.is_admin_or_superior()
    @commands.guild_only()
    @commands.group(name="buttonset")
    async def _button(self, ctx: commands.Context):
        """Configure button voice channel."""

    @_button.command(name="add")
    async def _button_add(self, ctx, category_id: str, room_id: int):
        """Whitelist a category and Channel to become a button."""
        dynamic_category_whitelist = await self.config.guild(
            ctx.guild
        ).category_with_button.get_raw()
        valid_categories = {
            f"{category.id}": category.name
            for category in ctx.guild.categories
            if category and f"{category.id}" not in dynamic_category_whitelist
        }

        if valid_categories and category_id not in valid_categories:
            await ctx.send(
                f"ERROR: {category_id} is not a valid category ID for {ctx.guild.name},"
                "these are the valid ones: ",
            )
            await ctx.send(box(json.dumps(valid_categories, indent=2), lang="json"))
        elif not valid_categories:
            await ctx.send(f"ERROR: No valid categories in {ctx.guild.name}")
        is_valid_voice_room = ctx.guild.get_channel(room_id)
        if not isinstance(is_valid_voice_room, discord.VoiceChannel):
            await ctx.send(f"ERROR: Room {room_id} is not a valid voice channel")

        guild_data = self.config.guild(ctx.guild)
        async with guild_data.category_with_button() as whitelist:
            whitelist.update({category_id: room_id})
            await ctx.send(f"Added {category_id} to the whitelist\nRooms ID is {room_id}")

    @_button.command(name="remove")
    async def _button_remove(self, ctx, category_id: str):
        """Removes category and voice channel button from whitelist."""
        guild_data = self.config.guild(ctx.guild)
        async with guild_data.category_with_button() as whitelist:
            if category_id in whitelist:
                del whitelist[str(category_id.id)]
                await ctx.send(f"Removed {category_id} from the whitelist")
            else:
                await ctx.send(f"Error: {category_id} is not a whitelisted category")

    @_button.group(name="role")
    async def _button_roles(self, ctx):
        """Whitelist roles to have special permission on user created rooms."""

    @_button_roles.command(name="manager")
    async def _button_roles_manager(self, ctx, *roles: commands.Greedy[discord.Role]):
        """Whitelist roles to have manager permission on user created rooms."""
        roles_ids = [role.id for role in roles]
        await self.config.guild(ctx.guild).user_created_voice_channels_bypass_roles.set(roles_ids)

    @_button_roles.command(name="muted")
    async def _button_roles_manager(self, ctx, *roles: commands.Greedy[discord.Role]):
        """Whitelist roles to have muted permission on user created rooms."""
        roles_ids = [role.id for role in roles]
        await self.config.guild(ctx.guild).mute_roles.set(roles_ids)

    async def on_guild_channel_delete(
        self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]
    ):
        if isinstance(channel, discord.VoiceChannel) and f"{channel.category.id}" in (
            await self.config.guild(channel.guild).category_with_button()
        ):
            logger.info(
                f"Custom Channel ({channel.id}) has been deleted checking if it exist in database"
            )
            channel_group = self.config.guild(channel.guild)
            async with channel_group.custom_channels() as channel_data:
                if f"{channel.id}" in channel_data:
                    logger.info(f"Custom Channel ({channel.id}) has been deleted from database")
                    del channel_data[f"{channel.id}"]

    async def on_guild_channel_create(
        self, channel: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel]
    ):
        if isinstance(channel, discord.VoiceChannel) and f"{channel.category.id}" in (
            await self.config.guild(channel.guild).category_with_button()
        ):
            logger.info(f"Custom Channel ({channel.id}) has been created adding to database")
            channel_group = self.config.guild(channel.guild)
            async with channel_group.custom_channels() as channel_data:
                data = {channel.id: channel.name}
                channel_data.update(data)

    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        whitelist = await self.config.guild(member.guild).category_with_button()
        user_created_channels = await self.config.guild(member.guild).user_created_voice_channels()
        if (
            after
            and after.channel
            and after.channel.category
            and f"{after.channel.category.id}" in whitelist
            and after.channel.id == whitelist[f"{after.channel.category.id}"]
        ):
            logger.info(f"User joined {after.channel.name} creating a new room")
            max_position = max([channel.position for channel in after.channel.category.channels])
            overwrites = await self._get_overrides(after.channel or before.channel, member)
            logger.info(f"Creating channel: Rename me - {member}")
            created_channel = await member.guild.create_voice_channel(
                name=f"Rename me - {member}",
                category=after.channel.category,
                overwrites=overwrites,
                position=max_position + 1,
                reason=f"{member.display_name} created a custom voice room",
                bitrate=member.guild.bitrate_limit,
            )
            logger.info(f"Moving {member.display_name} to : Rename me - {member}")
            await member.edit(
                voice_channel=created_channel,
                reason=f"Moving {member.display_name} to newly created custom room",
            )
            logger.info(f"User {member.display_name} has been moved to: Rename me - {member}")
            guild_group = self.config.guild(member.guild)
            async with guild_group.user_created_voice_channels() as user_voice:
                logger.info(
                    f"Adding {created_channel.name} to the database ({created_channel.id})"
                )
                user_voice.update({created_channel.id: created_channel.id})
            member_group = self.config.member(member)
            async with member_group.currentRooms() as user_voice:
                logger.info(f"Adding {created_channel.name} to user rooms ({created_channel.id})")
                user_voice.update({created_channel.id: created_channel.id})

        await self.channel_cleaner(before, after, member.guild, user_created_channels)

    async def _get_overrides(self, channel, owner=None):
        guild = channel.guild
        overwrites = {}
        if owner:
            overwrites.update({owner: creator_permissions})
        overwrites.update({guild.default_role: default_permission})
        for role_id in await self.config.guild(guild).user_created_voice_channels_bypass_roles():
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    overwrites.update({role: admin_permissions})
        for role_id in await self.config.guild(guild).mute_roles():
            if role_id:
                role = guild.get_role(role_id)
                if role:
                    overwrites.update({role: muted_permissions})
        return overwrites

    async def channel_cleaner(self, before, after, guild, user_created_channels):
        logger.info("Running channel_cleaner")
        if (
            before
            and before.channel
            and before.channel != after.channel
            and f"{before.channel.id}" in user_created_channels
        ):
            logger.info(
                f"{before.channel.name} was a user created room checking if it needs to be deleted"
            )
            delete_id = {}
            data = await self.config.guild(guild).user_created_voice_channels()

            for channel_id_str, channel_id in data.items():
                channel = guild.get_channel(channel_id)
                if channel and sum(1 for _ in channel.members) < 1:
                    logger.info(f"{channel.name} is empty trying to delete it")
                    await asyncio.sleep(5)
                    try:
                        await channel.delete(reason="User created room is empty cleaning up")
                        logger.info(f"{channel.name} has been removed")
                    except discord.NotFound:
                        logger.info(f"{channel.name} does not exist and couldn't be deleted")
                    delete_id.update({channel_id_str: channel_id})

            for player in await self.config.all_members(guild):
                member = guild.get_member(player)
                member_group = self.config.member(member)
                async with member_group.currentRooms() as user_voice:
                    for room in delete_id.keys():
                        if room in user_voice:
                            del user_voice[room]

            custom_channels = await self.config.guild(guild).user_created_voice_channels()
            custom_channels_to_keep = {
                k: v for k, v in custom_channels.items() if k not in delete_id
            }
            await self.config.guild(guild).user_created_voice_channels.set(custom_channels_to_keep)

    async def clean_up_custom_channels(self):
        with contextlib.suppress(asyncio.CancelledError):
            await self.bot.wait_until_ready()
            guilds = self.bot.guilds
            timer = 7200
            while guilds and True:
                logger.info(f"clean_up_custom_channels scheduled run started")
                guilds = self.bot.guilds
                for guild in guilds:
                    keep_id = {}
                    data = await self.config.guild(guild).user_created_voice_channels()
                    for channel_id_str, channel_id in data.items():
                        channel = guild.get_channel(channel_id)
                        if channel:
                            logger.info(f"Checking if {channel.name} is empty")
                            if sum(1 for _ in channel.members) < 1:
                                logger.info(f"{channel.name} is empty queueing it for deletion")
                                await asyncio.sleep(5)
                                await channel.delete(
                                    reason="User created channel was empty during cleanup cycle"
                                )
                                logger.info(f"{channel.name} has been deleted")
                            else:
                                logger.info(f"{channel.name} is not empty")
                                keep_id.update({channel_id_str: channel_id})
                    await self.config.guild(guild).user_created_voice_channels.set(keep_id)
                logger.info(
                    f"clean_up_custom_channels scheduled has finished sleeping for {timer}s"
                )
                await asyncio.sleep(timer)
