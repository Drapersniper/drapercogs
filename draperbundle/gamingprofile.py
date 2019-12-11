# -*- coding: utf-8 -*-
import asyncio
import contextlib
import logging
import time
from datetime import datetime, timezone
from operator import itemgetter
from typing import Union

import aiohttp
import discord
from discord.ext.commands.converter import Greedy
from redbot.core import commands, checks
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .config_holder import ConfigHolder
from .constants import CONTINENT_DATA
from .utilities import (
    update_profile,
    account_adder,
    update_member_atomically,
    add_username_hyperlink,
    get_all_by_platform,
    get_date_time,
    get_date_string,
    get_supported_platforms,
    get_role_named,
    get_member_activity,
)

logger = logging.getLogger("red.drapercogs.profile")


class GamingProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.profileConfig = ConfigHolder.GamingProfile
        self.config = ConfigHolder.AccountManager
        self._cache = {}
        self._task = self.bot.loop.create_task(self._save_to_config())

    @commands.group(name="profile")
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def _profile(self, ctx: commands.Context):
        """Managers a user profile"""

    @commands.guild_only()
    @checks.bot_has_permissions(manage_roles=True)
    @_profile.command(name="setup")
    async def _profile_setup(self, ctx: commands.Context):
        """Set up the environment needed by creating the required roles."""
        countries = list(CONTINENT_DATA.values())
        roles = countries + ["No Profile", "Has Profile"]
        for role in roles:
            await ctx.guild.create_role(
                name=role, mentionable=False, hoist=False, reason="Profile Setup"
            )

    @_profile.command(name="create", aliases=["make"])
    async def _profile_create(self, ctx: commands.Context):
        """Creates and sets up or updates an existing profile"""
        author = ctx.author
        guild = ctx.guild
        discord_user_name = str(author)
        user_data = {
            "country": None,
            "discord_user_id": author.id,
            "discord_true_name": author.name,
            "discord_user_name": discord_user_name,
            "identifier": author.id,
            "zone": None,
            "timezone": None,
            "language": None,
        }
        try:
            await ctx.author.send(
                "Creating your profile\nLet's continue here (We don't want to spam the other chat!)"
            )
            await ctx.author.send("Do you want to setup your profile now? ('y'/'n')")
        except discord.Forbidden:
            return await ctx.send(f"I can't PM you, {ctx.author.mention}")

        def check(m):
            return m.author == author and isinstance(m.channel, discord.DMChannel)

        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower() in ["y", "yes"]:
            role_to_add = []
            role_to_remove = []
            user_data = await update_profile(self.bot, user_data, author)
            accounts = await account_adder(self.bot, author)
            logger.info(f"profile_create: {author.display_name} Accounts:{accounts}")
            await self.profileConfig.user(author).discord_user_id.set(
                user_data.get("discord_user_id")
            )
            await self.profileConfig.user(author).discord_user_name.set(
                user_data.get("discord_user_name")
            )
            await self.profileConfig.user(author).discord_true_name.set(
                user_data.get("discord_true_name")
            )
            await self.profileConfig.user(author).country.set(user_data.get("country"))
            await self.profileConfig.user(author).zone.set(user_data.get("zone"))
            await self.profileConfig.user(author).timezone.set(user_data.get("timezone"))
            await self.profileConfig.user(author).language.set(user_data.get("language"))
            if user_data.get("subzone"):
                await self.profileConfig.user(author).subzone.set(user_data.get("subzone"))
            if accounts:
                accounts_group = self.config.user(author)
                async with accounts_group.account() as services:
                    for platform, username in accounts.items():
                        account = {platform: username}
                        services.update(account)
            if getattr(author, "guild"):
                doesnt_have_profile_role = get_role_named(ctx.guild, "No Profile")
                has_profile_role = get_role_named(ctx.guild, "Has Profile")
                continent_role = user_data.get("zone")
                role_names = [role.name for role in author.roles]
                if has_profile_role:
                    role_to_add.append(has_profile_role)
                if continent_role and continent_role not in role_names:
                    role = discord.utils.get(author.guild.roles, name=continent_role)
                    if role:
                        role_to_add.append(role)
                zone_roles_user_has = [x for x in list(CONTINENT_DATA.values()) if x in role_names]
                if len(zone_roles_user_has) > 1 or not continent_role:
                    roles = [
                        discord.utils.get(author.guild.roles, name=role_name)
                        for role_name in zone_roles_user_has
                        if discord.utils.get(author.guild.roles, name=role_name).name
                        != continent_role
                    ]
                    if roles:
                        role_to_remove += roles
                        role_to_remove.append(doesnt_have_profile_role)

                await update_member_atomically(author, give=role_to_add, remove=role_to_remove)

    @_profile.command(name="update")
    async def _profile_update(self, ctx: commands.Context):
        """Updates an existing profile"""
        role_to_add = []
        role_to_remove = []
        author = ctx.author
        user = {"country": None, "timezone": None, "language": None, "zone": None}
        try:
            await ctx.author.send(
                "Updating your profile\nLet's continue here(We don't want to spam the other chat!)",
            )
        except discord.Forbidden:
            return await ctx.author.send("I can't PM you", send_first=f"{ctx.author.mention}")
        user = await update_profile(self.bot, user, author)
        await self.profileConfig.user(author).country.set(user.get("country"))
        await self.profileConfig.user(author).zone.set(user.get("zone"))
        await self.profileConfig.user(author).timezone.set(user.get("timezone"))
        await self.profileConfig.user(author).language.set(user.get("language"))
        if user.get("subzone"):
            await self.profileConfig.user(author).subzone.set(user.get("subzone"))
        accounts = await account_adder(self.bot, author)
        logger.info(f"profile_update: {author.display_name} Accounts:{accounts}")
        if getattr(author, "guild"):
            if accounts:
                accounts_group = self.config.user(author)
                async with accounts_group.account() as services:
                    for platform, username in accounts.items():
                        account = {platform: username}
                        services.update(account)
            continent_role = user.get("zone")
            role_names = [role.name for role in author.roles]
            if continent_role and continent_role not in role_names:
                role = discord.utils.get(author.guild.roles, name=continent_role)
                if role:
                    role_to_add.append(role)
            zone_roles_user_has = [x for x in list(CONTINENT_DATA.values()) if x in role_names]
            if len(zone_roles_user_has) > 1 or not continent_role:
                roles = [
                    discord.utils.get(author.guild.roles, name=role_name)
                    for role_name in zone_roles_user_has
                    if discord.utils.get(author.guild.roles, name=role_name).name != continent_role
                ]
                if roles:
                    role_to_remove += roles
            await update_member_atomically(author, give=role_to_add, remove=role_to_remove)

        await ctx.author.send("I have updated your profile")

    @_profile.group(name="show", aliases=["display", "get"], invoke_without_command=True)
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def _profile_show(self, ctx: commands.Context):
        """Shows profiles for all members who are specified"""
        if ctx.invoked_subcommand is None:
            member = ctx.author
            embed = await self.get_member_profile(ctx, member)
            if embed:
                await ctx.send(embed=embed)

    @_profile_show.command(name="member")
    async def _profile_show_member(
        self, ctx: commands.Context, members: Greedy[discord.User] = None
    ):
        """Shows a members profile"""
        if not members:
            return await ctx.send_help()
        else:
            embed_list = []
            members = list(set(members))
            for member in members:
                if member is None:
                    continue
                embed = None
                embed = await self.get_member_profile(ctx, member)
                if embed and isinstance(embed, discord.Embed):
                    embed_list.append(embed)
            if embed_list:
                await menu(ctx, embed_list, DEFAULT_CONTROLS)

    @_profile_show.command(name="service")
    async def _profile_show_service(self, ctx: commands.Context, *, platform=None):
        """All members of a specific service"""
        if not platform:
            return await ctx.send_help()
        guild = ctx.guild
        is_dm = not guild
        logo = (await ConfigHolder.LogoData.custom("LOGOS").get_raw()).get(platform)

        if platform:
            data = await get_all_by_platform(platform=platform, guild=guild, pm=is_dm)
            if data:
                usernames = ""
                discord_names = ""
                embed_list = []
                for username, _, mention, _, steamid in sorted(data, key=itemgetter(3, 1)):
                    if username and mention:
                        username = add_username_hyperlink(platform, username, _id=steamid)
                        if (
                            len(usernames + f"{username}\n") > 1000
                            or len(discord_names + f"{mention}\n") > 1000
                        ):
                            embed = discord.Embed(title=f"{platform.title()} usernames",)
                            embed.add_field(name=f"Discord ID", value=discord_names, inline=True)
                            embed.add_field(name=f"Usernames", value=usernames, inline=True)
                            if logo:
                                embed.set_thumbnail(url=logo)
                            embed_list.append(embed)
                            usernames = ""
                            discord_names = ""
                        usernames += f"{username}\n"
                        discord_names += f"{mention}\n"
                if usernames:
                    embed = discord.Embed(title=f"{platform.title()} usernames")
                    embed.add_field(name=f"Discord ID", value=discord_names, inline=True)
                    embed.add_field(name=f"Usernames", value=usernames, inline=True)
                    if logo:
                        embed.set_thumbnail(url=logo)
                    embed_list.append(embed)
                await menu(
                    ctx,
                    pages=embed_list,
                    controls=DEFAULT_CONTROLS,
                    message=None,
                    page=0,
                    timeout=60,
                )
                embed_list = []
            else:
                return await ctx.send(f"No one has an account registered with {platform.title()}")

    @_profile_show.command(name="delete", aliases=["purge", "remove"])
    async def _profile_delete(self, ctx: commands.Context):
        """Deletes your profile permanently"""
        try:
            await ctx.author.send(
                "This cannot be undone and you will have to create a new profile, "
                "do you want to continue? (y/n)",
            )
        except discord.Forbidden:
            return await ctx.send(f"I can't PM you, {ctx.author.mention}")

        def check(m):
            return m.author == ctx.author and isinstance(m.channel, discord.DMChannel)

        msg = await self.bot.wait_for("message", check=check)
        if msg and msg.content.lower() in ["y", "yes"]:
            user_group = self.profileConfig.user(ctx.author)
            async with user_group() as user_data:
                user_data.clear()
            account_group = self.config.user(ctx.author)
            async with account_group() as account_data:
                account_data.clear()

            await ctx.author.send(f"To created a new one please run `{ctx.prefix}profile create`",)
        else:
            await ctx.author.send("Your profile hasn't been touched")

    @commands.Cog.listener()
    async def on_message_without_command(self, message):
        self._cache[message.author.id] = int(time.time())

    @commands.Cog.listener()
    async def on_typing(
        self,
        channel: discord.abc.Messageable,
        user: Union[discord.User, discord.Member],
        when: datetime,
    ):
        self._cache[user.id] = int(time.time())

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        self._cache[after.author.id] = int(time.time())

    @commands.Cog.listener()
    async def on_reaction_remove(
        self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]
    ):
        self._cache[user.id] = int(time.time())

    @commands.Cog.listener()
    async def on_reaction_add(
        self, reaction: discord.Reaction, user: Union[discord.Member, discord.User]
    ):
        self._cache[user.id] = int(time.time())

    async def get_member_profile(self, ctx: commands.Context, member: discord.Member):
        entries_to_remove = (
            "discord_user_id",
            "discord_user_name",
            "discord_true_name",
            "guild_display_name",
            "is_bot",
            "zone",
            "subzone",
            "seen",
            "trial",
            "nickname_extas",
        )
        data = await self.profileConfig.user(member).get_raw()
        last_seen = None
        if data.get("discord_user_id"):
            if member:
                last_seen = self._cache.get(member.id) or await self.profileConfig.user(member).seen()

            if last_seen:
                last_seen_datetime = get_date_time(last_seen)
                last_seen_text = get_date_string(last_seen_datetime)
            else:
                last_seen_datetime = None
                last_seen_text = ""
            description = ""
            for k in entries_to_remove:
                data.pop(k, None)
            accounts = await self.config.user(member).account()
            if accounts:
                accounts = {
                    key: value for key, value in accounts.items() if value and value != "None"
                }
            header = ""
            activity = get_member_activity(member)
            if activity:
                header += f"{activity}\n"
            description += header
            for key, value in data.items():
                if value:
                    description += f"{key.title()}: {value} | "
            description = description.rstrip("| ")
            description = description.strip()
            if description:
                description += "\n\n"
            embed = discord.Embed(title=f"Your Gaming Profile", description=description,)
            if accounts:
                platforms = await get_supported_platforms(lists=False)
                services = ""
                usernames = ""
                steamid = None
                for service, username in sorted(accounts.items()):
                    platform_name = platforms.get(service, {}).get("name")

                    if platform_name:
                        if platform_name.lower() == "steam":
                            steamid = accounts.get("steamid", None)
                        if platform_name.lower() == "spotify":
                            steamid = accounts.get("spotifyid", None)
                        username = add_username_hyperlink(platform_name, username, _id=steamid)
                        services += f"{platform_name}\n"
                        usernames += f"{username}\n"
                services.strip()
                usernames.strip()
                embed.add_field(name="Services", value=services)
                embed.add_field(name="Usernames", value=usernames)
            footer = ""
            if last_seen_datetime:
                if last_seen_text == "Now":
                    footer += "Currently online"
                else:
                    footer += f"Last online: {last_seen_text}"
            footer.strip()
            if footer:
                embed.set_footer(text=footer)
            avatar = member.avatar_url or member.default_avatar_url
            embed.set_author(name=member.display_name, icon_url=avatar)
            return embed
        else:
            mention = "You don't" if ctx.author == member else f"{member.mention} doesn't"
            await ctx.send(
                f"{mention} have a profile with me\nTo create one say `{ctx.prefix}profile create`",
            )
            return None

    @_profile.group(name="profile", case_insensitive=True)
    async def _profile_username(self, ctx: commands.Context):
        """Manage your service usernames"""

    @_profile_username.command(name="add", aliases=["+"])
    async def _profile_username_add(self, ctx: commands.Context):
        """Adds/updates an account for the specified service"""
        try:
            accounts = await account_adder(self.bot, ctx.author)
        except discord.Forbidden:
            return await ctx.send(f"I can't PM you, {ctx.author.mention}")
        logger.info(f"account_add: {ctx.author.display_name} Accounts:{accounts}")

        if accounts:
            accounts_group = self.config.user(ctx.author)
            async with accounts_group.account() as services:
                for platform, username in accounts.items():
                    account = {platform: username}
                    services.update(account)
            await ctx.author.send("I've added your accounts to your profile")
        else:
            await ctx.author.send("No accounts to add to your profile")

    @_profile_username.command(name="remove", aliases=["delete", "purge", "-"])
    async def account_remove(self, ctx: commands.Context, *args):
        """Removes an account from the specified service"""
        supported_platforms = await get_supported_platforms(supported=True)
        if len(args) == 1:
            platform = args[0].lower()
        else:
            platform = None
        try:
            if len(args) == 1 and platform in supported_platforms:
                account_group = self.config.user(ctx.author)
                async with account_group.account() as services:
                    deleted_data = services.pop(platform)
                if deleted_data:
                    await ctx.send(
                        f"I've deleted your {platform.title()} username: {deleted_data}",
                    )
                else:
                    await ctx.send(f"You don't have a {platform.title()} username with me")
            elif len(args) == 1 and platform not in supported_platforms:
                embedError = discord.Embed(title="Unsupported Platform")
                embed = discord.Embed(title="Supported Platforms are:")
                platforms = await get_supported_platforms()
                for command, name in platforms:
                    embed.add_field(name=name, value=f"Command: {command}", inline=False)
                await ctx.author.send(embed=embedError)
                await ctx.author.send(embed=embed)

            elif len(args) < 1:
                embed = discord.Embed(title="Too few arguments passed")
                embed.add_field(
                    name="Usage",
                    value=f"{ctx.prefix}platform add [platform] [username]",
                    inline=False,
                )
                await ctx.author.send(embed=embed)

            else:
                embed = discord.Embed(title="Too many arguments passed")
                embed.add_field(
                    name="Usage",
                    value=f"{ctx.prefix}platform add [platform] [username] * If your username has spaces make sure to add quotes around it",
                    inline=False,
                )
                await ctx.author.send(embed=embed)
        except discord.Forbidden:
            return await ctx.send(f"I can't PM you, {ctx.author.mention}")

    def cog_unload(self):
        self.bot.loop.create_task(self._clean_up())

    async def _clean_up(self):
        if self._task:
            self._task.cancel()
        if self._cache:
            group = self.profileConfig._get_base_group(self.config.USER)  # Bulk update to config
            async with group.all() as new_data:
                for member_id, seen in self._cache.items():
                    if str(member_id) not in new_data:
                        new_data[str(member_id)] = {"seen": 0}
                    new_data[str(member_id)]["seen"] = seen

    async def _save_to_config(self):
        await self.bot.wait_until_ready()
        with contextlib.suppress(asyncio.CancelledError):
            while True:
                users_data = self._cache.copy()
                self._cache = {}
                group = self.profileConfig._get_base_group(
                    self.config.USER
                )  # Bulk update to config
                async with group.all() as new_data:
                    for member_id, seen in users_data.items():
                        if str(member_id) not in new_data:
                            new_data[str(member_id)] = {"seen": 0}
                        new_data[str(member_id)]["seen"] = seen
                await asyncio.sleep(60)
