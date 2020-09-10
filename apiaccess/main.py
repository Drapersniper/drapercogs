import asyncio
import contextlib
import functools
import json
import logging
from copy import copy
from dataclasses import dataclass
from typing import Mapping, Optional, Set, Union

import aiohttp
import discord
from discord.ext.commands import MissingAnyRole, NoPrivateMessage
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands import check
from redbot.core.utils.chat_formatting import box, pagify
from tabulate import tabulate

from apiaccess.menus import LeaderboardSource, SimpleHybridMenu

GUILD_ID = 749205869530578964
API_ENDPOINT = "http://172.40.0.5:8000"
log = logging.getLogger("red.drapercogs.APIManager")


@dataclass
class RequesterObject:
    user_id: str
    is_blacklisted: bool = False
    is_superuser: bool = False
    is_admin: bool = False
    is_mod: bool = False
    is_contributor: bool = False
    is_user: bool = False
    is_guest: bool = False
    name: str = "Unauthenticated"
    entries_submitted: int = 0
    token: Optional[str] = None
    updated_on: str = None
    blacklisted_on: str = None
    registered_on: str = None
    md5: str = None
    id: int = None
    can_delete: bool = False
    can_post: bool = False
    can_read: bool = False

    def __post_init__(self):
        self.is_blacklisted = bool(int(self.is_blacklisted))
        self.is_superuser = bool(int(self.is_superuser))
        self.is_admin = bool(int(self.is_admin))
        self.is_mod = bool(int(self.is_mod))
        self.is_contributor = bool(int(self.is_contributor))
        self.is_user = bool(int(self.is_user))
        self.is_guest = bool(int(self.is_guest))
        if not self.name:
            self.name = "Unauthenticated"
        else:
            if type(self.name) is bytes:
                self.name = self.name.decode()
        if not self.token:
            self.token = None
        else:
            if type(self.token) is bytes:
                self.token = self.token.decode()
        self.user_id = str(self.user_id)
        self.entries_submitted = int(self.entries_submitted)
        self.can_read = not self.is_blacklisted and any(
            [
                self.is_user,
                self.is_contributor,
                self.is_mod,
                self.is_admin,
                self.is_superuser,
            ]
        )
        self.can_post = self.can_read and not self.is_user
        self.can_delete = self.can_post and not self.is_contributor

    def to_json(self):
        return dict(
            user_id=self.user_id,
            entries_submitted=self.entries_submitted,
            is_guest=self.is_guest,
            is_user=self.is_user,
            is_contributor=self.is_contributor,
            is_mod=self.is_mod,
            is_admin=self.is_admin,
            is_superuser=self.is_superuser,
            is_blacklisted=self.is_blacklisted,
            name=self.name,
        )

    def to_json_full(self):
        return dict(
            user_id=self.user_id,
            entries_submitted=self.entries_submitted,
            is_guest=self.is_guest,
            is_user=self.is_user,
            is_contributor=self.is_contributor,
            is_mod=self.is_mod,
            is_admin=self.is_admin,
            is_superuser=self.is_superuser,
            is_blacklisted=self.is_blacklisted,
            name=self.name,
            token=self.token,
        )


def in_guild():
    def predicate(ctx):
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            raise NoPrivateMessage()
        guild: discord.Guild = ctx.bot.get_guild(GUILD_ID)
        member = guild.get_member(ctx.author.id)
        if not member:
            return False
        return True

    return check(predicate)


def has_any_role_in_guild(*items):
    def predicate(ctx):
        if not isinstance(ctx.channel, discord.abc.GuildChannel):
            raise NoPrivateMessage()
        guild: discord.Guild = ctx.bot.get_guild(GUILD_ID)
        member = guild.get_member(ctx.author.id)
        if not member:
            return False
        if guild.owner.id == member.id:
            return True

        getter = functools.partial(discord.utils.get, member.roles)
        if any(
            getter(id=item) is not None if isinstance(item, int) else getter(name=item) is not None
            for item in items
        ):
            return True
        raise MissingAnyRole(items)

    return check(predicate)


class APIManager(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.any_role: Set[discord.Role] = set()
        self.user_role: Optional[discord.Role] = None
        self.contributor_role: Optional[discord.Role] = None
        self.mod_role: Optional[discord.Role] = None
        self.admin_role: Optional[discord.Role] = None
        self.banned_role: Optional[discord.Role] = None
        self.bot_role: Optional[discord.Role] = None
        self.headers: Mapping = {}
        self.guild: discord.Guild = self.bot.get_guild(GUILD_ID)
        self.cog_is_ready: asyncio.Event = asyncio.Event()
        self.start_up_task: asyncio.Task = asyncio.create_task(self.init())

    async def init(self):
        await self.bot.wait_until_red_ready()
        self.guild: discord.Guild = self.bot.get_guild(GUILD_ID)
        self.user_role = self.guild.get_role(749329381918244924)
        self.contributor_role = self.guild.get_role(749329344433750157)
        self.mod_role = self.guild.get_role(749329319616184481)
        self.admin_role = self.guild.get_role(749329286376456353)
        self.banned_role = self.guild.get_role(749329677067223081)
        self.bot_role = self.guild.get_role(749395257623445615)
        self.any_role = {
            self.user_role,
            self.contributor_role,
            self.mod_role,
            self.admin_role,
            self.banned_role,
        }
        self.headers = {
            "Authorization": (await self.bot.get_shared_api_tokens("audiodb")).get("api_key")
        }
        self.cog_is_ready.set()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        await self.assign_role(member=member, reason="Joined The Server")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.guild.id != GUILD_ID:
            return
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{API_ENDPOINT}/api/v2/users/user/{member.id}",
                headers=self.headers,
                params={"revoke_token": str(True).lower()},
            ) as resp:
                await resp.json()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.channel.id != 749207620249976892:
            return
        if len(message.content) < 32:
            return
        target_channel = message.guild.get_channel(749399885081477190)
        with contextlib.suppress(discord.HTTPException):
            new_message: discord.Message = await target_channel.send(
                f"Message sent by : {message.author.mention}\n{message.content[:1800]}"
            )
            await message.delete()
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_ENDPOINT}/api/v2/users/user",
                headers=self.headers,
                params={
                    "user_id": str(message.author.id),
                    "name": str(message.author),
                    "is_user": str(True).lower(),
                },
            ) as resp:
                if resp.status == 200:
                    await resp.json()
                    await new_message.add_reaction("\N{WHITE HEAVY CHECK MARK}")
                    await self.assign_role(
                        member=message.author, reason="Has Been Given The Role Automatically"
                    )
                    await self.send_token(message=message)
                elif resp.status == 401:
                    await new_message.add_reaction("\N{CROSS MARK}")
                elif resp.status == 409:
                    await new_message.add_reaction(
                        "\N{ANTICLOCKWISE DOWNWARDS AND UPWARDS OPEN CIRCLE ARROWS}"
                    )
                    await self.assign_role(
                        member=message.author, reason="Has Been Given The Role Automatically"
                    )
                    await self.send_token(message=message)
                else:
                    await new_message.add_reaction(
                        "\N{EXCLAMATION QUESTION MARK}\N{VARIATION SELECTOR-16}"
                    )

    @commands.command(name="showinfo")
    @commands.guild_only()
    @has_any_role_in_guild(
        749329286376456353, 749329319616184481, 749329344433750157, 749329381918244924
    )
    async def command_showinfo(
        self, ctx: commands.Context, *, user: Optional[Union[discord.User, int]] = None
    ):
        """Show user info."""
        if user is not None:
            user_id = user.id if isinstance(user, discord.abc.User) else user
        else:
            user_id = ctx.author.id
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/cached/{user_id}", headers=self.headers
            ) as resp:
                if resp.status == 200:
                    new_data = {}
                    data = await resp.json()
                    user = RequesterObject(**data)
                    new_data["Name"] = f"[{user.name}]"
                    new_data["User ID"] = f"[{user.user_id}]"
                    new_data["Entries Submitted"] = f"[{user.entries_submitted}]"
                    new_data["Can Read"] = f"[{user.can_read}]"
                    new_data["Can Post"] = f"[{user.can_post}]"
                    new_data["Can Delete"] = f"[{user.can_delete}]"
                    return await ctx.send(
                        box(
                            tabulate(
                                list(new_data.items()),
                                missingval="?",
                                tablefmt="plain",
                            ),
                            lang="ini",
                        )
                    )
                else:
                    return await ctx.send("Failed to get user info")

    @commands.command(name="mytoken")
    @commands.guild_only()
    @commands.cooldown(1, 600, commands.BucketType.user)
    async def command_mytoken(self, ctx: commands.Context):
        """Get your user Global API details."""
        user_id = ctx.author.id
        if not self.guild.get_member(user_id):
            return await ctx.send(
                "You aren't in the support server your token is linked to the server, join https://discord.gg/zkmDzhs so that you can request access."
            )
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/user/{user_id}", headers=self.headers
            ) as resp:
                if resp.status == 200:
                    new_data = {}
                    data = await resp.json()
                    log.info(
                        f"{ctx.author} ({ctx.author.id}) requested their token: {data.get('user_id')}"
                    )
                    if int(data.get("user_id", 0)) != ctx.author.id:
                        return await ctx.send("Failed to get user info")
                    try:
                        user = RequesterObject(**data)

                        new_data["Name"] = f"[{user.name}]"
                        new_data["User ID"] = f"[{user.user_id}]"
                        new_data["Entries Submitted"] = f"[{user.entries_submitted}]"
                        new_data["Can Read"] = f"[{user.can_read}]"
                        new_data["Can Post"] = f"[{user.can_post}]"
                        new_data["Can Delete"] = f"[{user.can_delete}]"

                        await ctx.author.send(
                            box(
                                tabulate(
                                    list(new_data.items()),
                                    missingval="?",
                                    tablefmt="plain",
                                ),
                                lang="ini",
                            )
                        )
                        if user.token is not None:
                            await ctx.author.send(
                                f"Use: `[p]set api audiodb api_key {user.token}` to set this key on your bot."
                            )
                    except discord.HTTPException:
                        ctx.command.reset_cooldown(ctx)
                        await ctx.send("I can't DM you.")
                    member = self.guild.get_member(ctx.author.id)
                    await self.assign_role(
                        member=member, reason="Has Been Given The Role Manually"
                    )
                elif resp.status == 404:
                    return await ctx.send(
                        "You haven't been registered with in the API, join https://discord.gg/zkmDzhs so that you can request access."
                    )
                else:
                    ctx.command.reset_cooldown(ctx)
                    return await ctx.send("Failed to get user info")

    @commands.command(name="apilb")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353, 749329319616184481, 749329344433750157)
    async def command_apilb(self, ctx: commands.Context):
        """Show the API Leaderboard."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/",
                headers=self.headers,
                params={"limit": 25},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    data = [
                        (i.get("entries_submitted"), i.get("user_id"), i.get("name"))
                        for i in data
                        if ((not i.get("is_blacklisted")) and i.get("token"))
                    ]
                    data.sort(key=lambda x: x[0], reverse=True)
                    await SimpleHybridMenu(
                        source=LeaderboardSource(data),
                        delete_message_after=True,
                        timeout=60,
                        clear_reactions_after=True,
                    ).start(ctx)

                else:
                    await ctx.send("Nothing found")

    @commands.command(name="apicleanup")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353, 749329319616184481)
    async def command_apicleanup(self, ctx: commands.Context):
        """Remove users from API if they aren't in the server."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/",
                headers=self.headers,
                params={"limit": 1000000},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    data = [i.get("user_id") for i in data if not i.get("is_blacklisted")]
                    for user_id in data:
                        member = self.guild.get_member(int(user_id))
                        if not member:
                            async with session.delete(
                                f"{API_ENDPOINT}/api/v2/users/user",
                                headers=self.headers,
                                params={"user_id": user_id},
                            ) as del_resp:
                                if del_resp.status == 200:
                                    del_data = await del_resp.json()
                                    log.info(
                                        f"User: {del_data.get('name')} ({del_data.get('user_id')}) has been deleted via d.apicleanup by {ctx.author}"
                                    )
                    await ctx.tick()
                else:
                    await ctx.send("Something went wrong.")

    @commands.command(name="apidecode")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353, 749329319616184481, 749329344433750157)
    async def command_apidecode(self, ctx: commands.Context, *, base64: str):
        """Decode a Lavalink base64 string."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/queries/decode",
                headers=self.headers,
                params={"query": base64},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    await ctx.send(box(json.dumps(data, indent=2, sort_keys=True), lang="json"))
                else:
                    await ctx.send("Nothing found")

    @commands.command(name="query")
    @commands.guild_only()
    @has_any_role_in_guild(
        749329286376456353, 749329319616184481, 749329344433750157, 749329381918244924
    )
    async def command_query(self, ctx: commands.Context, *, query: str):
        """Make a non spotify query"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/queries",
                headers=self.headers,
                params={"query": query},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for page in pagify(json.dumps(data, indent=2, sort_keys=True), shorten_by=16):
                        await ctx.send(box(page, lang="json"))
                else:
                    await ctx.send("Nothing found")

    @commands.command(name="spotify")
    @commands.guild_only()
    @has_any_role_in_guild(
        749329286376456353, 749329319616184481, 749329344433750157, 749329381918244924
    )
    async def command_spotify(self, ctx: commands.Context, author: str, *, title: str):
        """Make a spotify query"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/queries/spotify",
                headers=self.headers,
                params={"author": author, "title": title},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for page in pagify(json.dumps(data, indent=2, sort_keys=True), shorten_by=16):
                        await ctx.send(box(page, lang="json"))
                else:
                    await ctx.send("Nothing found")

    @commands.command(name="ytid")
    @commands.guild_only()
    @has_any_role_in_guild(
        749329286376456353, 749329319616184481, 749329344433750157, 749329381918244924
    )
    async def command_ytid(self, ctx: commands.Context, *, id: str):
        """Make a youtube id query"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/queries/es/search/youtube/id",
                headers=self.headers,
                params={"query": id},
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    for page in pagify(json.dumps(data, indent=2, sort_keys=True), shorten_by=16):
                        await ctx.send(box(page, lang="json"))
                else:
                    await ctx.send("Nothing found")

    @commands.command(name="apiban", cooldown_after_parsing=True)
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @has_any_role_in_guild(749329286376456353, 749329319616184481)
    async def command_apiban(self, ctx: commands.Context, *, user: Union[discord.User, int]):
        """Ban people from server and API."""
        if isinstance(user, discord.abc.User):
            user_name = str(user)
            user_id = user.id
        else:
            user = await self.bot.fetch_user(user)
            user_name = str(user)
            user_id = user.id

        member = self.guild.get_member(user_id)
        if member and not await self.is_allowed_by_hierarchy(ctx.author, member):
            return await ctx.send("I can't allow you to do that.")

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{API_ENDPOINT}/api/v2/users/ban/user/{user_id}",
                headers=self.headers,
                params={"name": user_name},
            ) as resp:
                if resp.status == 200:
                    new_data = {}
                    data = await resp.json()
                    interesting_key = [
                        "user_id",
                        "entries_submitted",
                        "name",
                        "is_contributor",
                        "is_mod",
                        "is_admin",
                        "is_blacklisted",
                        "updated_on",
                    ]
                    for key, value in data.items():
                        if key in interesting_key:
                            new_data[" ".join(key.split("_")).title()] = value
                    await ctx.send(
                        box(json.dumps(new_data, indent=2, sort_keys=True), lang="json")
                    )
        guild = self.guild
        with contextlib.suppress(discord.HTTPException):
            await guild.ban(user, reason=f"Requested by {ctx.author}", delete_message_days=1)
        await ctx.tick()

    @commands.command(name="apirevoke")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353, 749329319616184481)
    async def command_apirevoke(self, ctx: commands.Context, *, user: Union[discord.User, int]):
        """Revoke people's API access."""
        user_id = user.id if isinstance(user, discord.abc.User) else user
        member = self.guild.get_member(user_id)
        if not member:
            member = discord.Object(id=user_id)
        elif not await self.is_allowed_by_hierarchy(ctx.author, member):
            return await ctx.send("I can't allow you to do that.")
        await self.change_role(member=member, banned=True, revoke_token=True)
        if isinstance(member, discord.Member):
            await self.assign_role(
                member=member, reason=f"Has Been Given The Role Manually by {ctx.author}"
            )
        await ctx.tick()

    @commands.command(name="giveapiroles")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353, 749329319616184481)
    async def command_giveapiroles(self, ctx: commands.Context):
        """Assign role to users missing roles."""
        async with ctx.typing():
            for member in self.guild.members:
                if member.bot:
                    continue
                if member.id == member.guild.owner.id:
                    continue
                await self.assign_role(member=member, reason="Has Been Given The Role Manually")
        await ctx.tick()

    @commands.command(name="apicontributor")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353, 749329319616184481)
    async def command_apicontributor(self, ctx: commands.Context, user_id: int):
        """Elevate a user to contributor status."""
        member = self.guild.get_member(user_id)
        if not member:
            return
        if not await self.is_allowed_by_hierarchy(ctx.author, member):
            return await ctx.send("I can't allow you to do that.")
        await self.change_role(member=member, contrib=True)
        await self.assign_role(
            member=member, reason=f"Has Been Given The Role Manually by {ctx.author}"
        )
        await ctx.tick()

    @commands.command(name="apimod")
    @commands.guild_only()
    @has_any_role_in_guild(749329286376456353)
    async def command_apimod(self, ctx: commands.Context, user_id: int):
        """Elevate a user to mod status."""
        member = self.guild.get_member(user_id)
        if not member:
            return
        if not await self.is_allowed_by_hierarchy(ctx.author, member):
            return await ctx.send("I can't allow you to do that.")
        await self.change_role(member=member, mod=True)
        await self.assign_role(
            member=member, reason=f"Has Been Given The Role Manually by {ctx.author}"
        )
        await ctx.tick()

    @commands.command(name="apiadmin")
    @commands.guild_only()
    @commands.guildowner()
    async def command_apiadmin(self, ctx: commands.Context, user_id: int):
        """Elevate a user to admin status."""
        member = self.guild.get_member(user_id)
        if not member:
            return
        if not await self.is_allowed_by_hierarchy(ctx.author, member):
            return await ctx.send("I can't allow you to do that.")
        await self.change_role(member=member, admin=True)
        await self.assign_role(
            member=member, reason=f"Has Been Given The Role Manually by {ctx.author}"
        )
        await ctx.tick()

    async def assign_role(self, member: discord.Member, reason: str):
        if member.bot:
            with contextlib.suppress(Exception):
                await member.add_roles(self.bot_role)
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_ENDPOINT}/api/v2/users/user/{member.id}", headers=self.headers
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get("is_blacklisted"):
                        await member.edit(roles=[self.banned_role], reason=f"Banned User {reason}")
                    elif data.get("is_admin"):
                        await member.edit(
                            roles=[self.admin_role], reason=f"User With Access {reason}"
                        )
                    elif data.get("is_mod"):
                        await member.edit(
                            roles=[self.mod_role], reason=f"User With Access {reason}"
                        )
                    elif data.get("is_contributor"):
                        await member.edit(
                            roles=[self.contributor_role], reason=f"User With Access {reason}"
                        )
                    elif data.get("is_user"):
                        await member.edit(
                            roles=[self.user_role], reason=f"User With Access {reason}"
                        )

    async def change_role(
        self,
        member: discord.Member,
        admin: bool = False,
        mod: bool = False,
        contrib: bool = False,
        user: bool = False,
        banned: bool = False,
        revoke_token: bool = False,
    ):
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{API_ENDPOINT}/api/v2/users/user/{member.id}",
                headers=self.headers,
                params={
                    "revoke_token": str(revoke_token).lower(),
                    "blacklist": str(banned).lower(),
                    "renew_token": str(True).lower(),
                },
                json={
                    "is_admin": admin,
                    "is_mod": mod,
                    "is_contributor": contrib,
                    "is_user": user,
                    "is_guest": False,
                },
            ) as resp:
                return await resp.json()

    async def is_allowed_by_hierarchy(self, mod: discord.Member, user: discord.Member):
        is_special = await self.bot.is_owner(mod)
        return mod.top_role.position > user.top_role.position or is_special

    async def send_token(self, message: discord.Message):
        msg = copy(message)
        msg.content = f"d.mytoken"
        self.bot.dispatch("message", msg)
