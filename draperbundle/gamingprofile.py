# -*- coding: utf-8 -*-
import asyncio
import contextlib
import logging
import time
from collections import defaultdict
from datetime import datetime
from operator import itemgetter
from typing import Union

import aiohttp
import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu, start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

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
    has_a_profile,
)

log = logging.getLogger("red.drapercogs.profile")


class GamingProfile(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.profileConfig = ConfigHolder.GamingProfile
        self.config = ConfigHolder.AccountManager
        self._cache = {}
        self._task = self.bot.loop.create_task(self._save_to_config())
        self.config_cache = defaultdict(dict)

    @commands.group(name="gprofile")
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def _profile(self, ctx: commands.Context):
        """Managers a user profile"""

    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @_profile.command(name="setup")
    async def _profile_setup(self, ctx: commands.Context):
        """Set up the environment needed by creating the required roles."""
        countries = list(CONTINENT_DATA.values())
        roles = countries + ["No Profile", "Has Profile"]
        existing_roles = [r.name for r in ctx.guild.roles]
        for role in roles:
            if role not in existing_roles:
                await ctx.guild.create_role(
                    name=role, mentionable=False, hoist=False, reason="Profile Setup"
                )
        await ctx.tick()

    @commands.guild_only()
    @commands.bot_has_permissions(manage_roles=True)
    @_profile.command(name="rolemanager")
    async def _profile_role_management(self, ctx: commands.Context):
        """Toggle whether to manage roles."""
        async with self.profileConfig.guild(ctx.guild).all() as guild_data:
            current_role_management = guild_data["role_management"]
            guild_data["role_management"] = not current_role_management
            self.config_cache[ctx.guild.id] = not current_role_management

        if not current_role_management:
            await ctx.send(
                (
                    "Gaming profile will manage regional and profile roles, "
                    "run `{}gprofile setup` to ensure you have all the "
                    "required roles in the server."
                ).format(ctx.clean_prefix)
            )
        else:
            await ctx.send("Gaming profile will no longer touch user roles")

    @_profile.command(name="create", aliases=["make"])
    async def _profile_create(self, ctx: commands.Context):
        """Creates and sets up or updates an existing profile"""
        author = ctx.author
        user_data = {
            "country": None,
            "identifier": author.id,
            "zone": None,
            "timezone": None,
            "language": None,
        }
        try:
            await ctx.author.send(
                "Creating your profile\nLet's continue here (We don't want to spam the other chat!)"
            )
            exists_msg = await ctx.author.send("Do you want to setup your profile now?")
            start_adding_reactions(exists_msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(exists_msg, ctx.author)
            await self.bot.wait_for("reaction_add", check=pred)
        except discord.Forbidden:
            return await ctx.send(f"I can't DM you, {ctx.author.mention}")
        if pred.result:
            role_to_add = []
            role_to_remove = []
            new_user_data = await update_profile(self.bot, user_data, author)
            accounts = await account_adder(self.bot, author)
            log.debug(f"profile_create: {author.display_name} Accounts:{accounts}")
            async with self.profileConfig.user(author).all() as user_data:
                user_data.update(new_user_data)
            if accounts:
                accounts_group = self.config.user(author)
                async with accounts_group.account() as services:
                    for platform, username in accounts.items():
                        account = {platform: username}
                        services.update(account)
            if (
                getattr(author, "guild", None)
                and await self.profileConfig.guild(author.guild).role_management()
                and author.guild.me.guild_permissions.manage_roles
            ):
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
                zone_roles_user_has = [
                    x for x in list(CONTINENT_DATA.values()) if x in role_names
                ]
                if len(zone_roles_user_has) > 1 or not continent_role:
                    roles = [
                        discord.utils.get(author.guild.roles, name=role_name)
                        for role_name in zone_roles_user_has
                        if discord.utils.get(author.guild.roles, name=role_name).name
                        != continent_role
                    ]
                    roles = [r for r in roles if r]
                    if roles:
                        role_to_remove += roles
                        if doesnt_have_profile_role:
                            role_to_remove.append(doesnt_have_profile_role)

                await update_member_atomically(
                    ctx=ctx, member=author, give=role_to_add, remove=role_to_remove
                )
            await author.send("Done.")

    @_profile.command(name="update")
    async def _profile_update(self, ctx: commands.Context):
        """Updates an existing profile"""
        role_to_add = []
        role_to_remove = []
        author = ctx.author
        user = {"country": None, "timezone": None, "language": None, "zone": None}
        try:
            await ctx.author.send(
                "Updating your profile\nLet's continue here (We don't want to spam the other chat!)"
            )
        except discord.Forbidden:
            return await ctx.author.send(
                "I can't DM you", send_first=f"{ctx.author.mention}"
            )
        user = await update_profile(self.bot, user, author)
        async with self.profileConfig.user(author).all() as user_data:
            user_data.update(user)
        accounts = await account_adder(self.bot, author)
        log.debug(f"profile_update: {author.display_name} Accounts:{accounts}")
        if accounts:
            accounts_group = self.config.user(author)
            async with accounts_group.account() as services:
                for platform, username in accounts.items():
                    account = {platform: username}
                    services.update(account)
        if (
            getattr(author, "guild", None)
            and await self.profileConfig.guild(author.guild).role_management()
            and author.guild.me.guild_permissions.manage_roles
        ):
            continent_role = user.get("zone")
            role_names = [role.name for role in author.roles]
            if continent_role and continent_role not in role_names:
                role = discord.utils.get(author.guild.roles, name=continent_role)
                if role:
                    role_to_add.append(role)
            zone_roles_user_has = [
                x for x in list(CONTINENT_DATA.values()) if x in role_names
            ]
            if len(zone_roles_user_has) > 1 or not continent_role:
                roles = [
                    discord.utils.get(author.guild.roles, name=role_name)
                    for role_name in zone_roles_user_has
                    if discord.utils.get(author.guild.roles, name=role_name).name
                    != continent_role
                ]
                roles = [r for r in roles if r]
                if roles:
                    role_to_remove += roles
            await update_member_atomically(
                ctx=ctx, member=author, give=role_to_add, remove=role_to_remove
            )

        await ctx.author.send("I have updated your profile")

    @_profile.command(name="show", aliases=["display", "get"])
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def _profile_show(self, ctx: commands.Context, *member: discord.Member):
        """Shows profiles for all members who are specified"""
        members = member or [ctx.author]
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

    @_profile.command(name="list")
    @commands.guild_only()
    async def _profile_list_service(self, ctx: commands.Context, *, platform: str):
        """All members of a specific service"""
        guild = ctx.guild
        is_dm = not guild
        logo = (await ConfigHolder.LogoData.get_raw()).get(platform)
        if platform:
            data = await get_all_by_platform(platform=platform, guild=guild, pm=is_dm)
            if data:
                usernames = ""
                discord_names = ""
                embed_list = []
                for username, _, mention, _, steamid in sorted(
                    data, key=itemgetter(3, 1)
                ):
                    if username and mention:
                        username = add_username_hyperlink(
                            platform, username, _id=steamid
                        )
                        if (
                            len(usernames + f"{username}\n") > 1000
                            or len(discord_names + f"{mention}\n") > 1000
                        ):
                            embed = discord.Embed(title=f"{platform.title()} usernames")
                            embed.add_field(
                                name=f"Discord ID", value=discord_names, inline=True
                            )
                            embed.add_field(
                                name=f"Usernames", value=usernames, inline=True
                            )
                            if logo:
                                embed.set_thumbnail(url=logo)
                            embed_list.append(embed)
                            usernames = ""
                            discord_names = ""
                        usernames += f"{username}\n"
                        discord_names += f"{mention}\n"
                if usernames:
                    embed = discord.Embed(title=f"{platform.title()} usernames")
                    embed.add_field(
                        name=f"Discord ID", value=discord_names, inline=True
                    )
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
                return await ctx.send(
                    f"No one has an account registered with {platform.title()}"
                )

    @_profile.command(name="delete", aliases=["purge", "remove"])
    async def _profile_delete(self, ctx: commands.Context):
        """Deletes your profile permanently"""
        try:
            exists_msg = await ctx.author.send(
                "This cannot be undone and you will have to create a new profile, "
                "do you want to continue? (y/n)"
            )
            start_adding_reactions(exists_msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(exists_msg, ctx.author)
            await self.bot.wait_for("reaction_add", check=pred)
        except discord.Forbidden:
            return await ctx.send(f"I can't DM you, {ctx.author.mention}")

        if pred.result:
            user_group = self.profileConfig.user(ctx.author)
            async with user_group() as user_data:
                user_data.clear()
            account_group = self.config.user(ctx.author)
            async with account_group() as account_data:
                account_data.clear()
            await ctx.author.send(
                f"To created a new one please run `{self._profile_create.qualified_name}`"
            )
        else:
            await ctx.author.send("Your profile hasn't been touched")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        guild = after.guild
        role_to_remove = []
        role_to_add = []
        if self.config_cache[guild.id] == {}:
            self.config_cache[guild.id] = await self.profileConfig.guild(
                guild
            ).role_management()
        if not self.config_cache[guild.id]:
            return
        if guild and guild.me.guild_permissions.manage_roles:
            continent_role = await self.profileConfig.user(after).zone()
            role_names = [role.name for role in after.roles]
            if continent_role and continent_role not in role_names:
                role = discord.utils.get(after.guild.roles, name=continent_role)
                if role:
                    role_to_add.append(role)
            zone_roles_user_has = [
                x for x in list(CONTINENT_DATA.values()) if x in role_names
            ]
            if len(zone_roles_user_has) > 1 or not continent_role:
                roles = [
                    discord.utils.get(after.guild.roles, name=role_name)
                    for role_name in zone_roles_user_has
                    if discord.utils.get(after.guild.roles, name=role_name).name
                    != continent_role
                ]
                if roles:
                    role_to_remove += roles
            doesnt_have_profile_role = get_role_named(after.guild, "No Profile")
            has_profile_role = get_role_named(after.guild, "Has Profile")
            if await has_a_profile(after):
                if has_profile_role:
                    role_to_add.append(has_profile_role)
                if doesnt_have_profile_role:
                    role_to_remove.append(doesnt_have_profile_role)
            else:
                if doesnt_have_profile_role:
                    role_to_add.append(doesnt_have_profile_role)
                if has_profile_role:
                    role_to_remove.append(has_profile_role)
            if role_to_add or role_to_remove:
                await update_member_atomically(
                    ctx=after,
                    member=after,
                    give=role_to_add,
                    remove=role_to_remove,
                    member_update=True,
                )

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
        if data.get("identifier"):
            if member:
                last_seen = (
                    self._cache.get(member.id)
                    or await self.profileConfig.user(member).seen()
                )

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
                    key: value
                    for key, value in accounts.items()
                    if value and value != "None"
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
            embed = discord.Embed(title=f"Gaming Profile", description=description)
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
                        username = add_username_hyperlink(
                            platform_name, username, _id=steamid
                        )
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
            if ctx.author == member:
                await ctx.send(
                    "You don't have a profile with me\n"
                    f"To create one say `{self._profile_create.qualified_name}`"
                )
            else:
                await ctx.send(f"{member.mention} doesn't have a profile with me")
            return None

    @_profile.group(name="services", case_insensitive=True)
    async def _profile_username(self, ctx: commands.Context):
        """Manage your service usernames"""

    @_profile_username.command(name="add", aliases=["+"])
    async def _profile_username_add(self, ctx: commands.Context):
        """Adds/updates an account for the specified service"""
        try:
            accounts = await account_adder(self.bot, ctx.author)
        except discord.Forbidden:
            return await ctx.send(f"I can't DM you, {ctx.author.mention}")
        log.debug(f"account_add: {ctx.author.display_name} Accounts:{accounts}")

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
    async def account_remove(self, ctx: commands.Context, *, platform: str):
        """Removes an account from the specified service"""
        supported_platforms = await get_supported_platforms(supported=True)
        platform = platform.lower()
        try:
            if platform in supported_platforms:
                account_group = self.config.user(ctx.author)
                async with account_group.account() as services:
                    deleted_data = services.pop(platform)
                if deleted_data:
                    await ctx.send(
                        f"I've deleted your {platform.title()} username: {deleted_data}"
                    )
                else:
                    await ctx.send(
                        f"You don't have a {platform.title()} username with me"
                    )
            elif platform not in supported_platforms:
                platforms = await get_supported_platforms()
                pos_len = 3
                platforms_text = f"{'#':{pos_len}}\n"
                for number, (command, name) in enumerate(platforms, 1):
                    line = (
                        "{number}."
                        "    <{name}>\n"
                        " - Command:  < {scope} >\n".format(
                            number=number,
                            name=name,
                            command=command,
                        )
                    )
                    platforms_text += line
                pages = list(pagify(platforms_text, page_length=1800))
                await menu(ctx.author, pages, DEFAULT_CONTROLS)
        except discord.Forbidden:
            return await ctx.send(f"I can't DM you, {ctx.author.mention}")

    def cog_unload(self):
        self.bot.loop.create_task(self._clean_up())

    async def _clean_up(self):
        if self._task:
            self._task.cancel()
        if self._cache:
            group = self.profileConfig._get_base_group(
                self.config.USER
            )  # Bulk update to config
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
