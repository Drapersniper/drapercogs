import asyncio
import logging
from typing import Mapping, Optional, Union

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from tabulate import tabulate

from .api import API
from .checks import is_api_admin, is_api_user, is_api_mod, is_not_api_user
from .menus import LeaderboardSource, SimpleHybridMenu
from .utils import User

log = logging.getLogger("red.drapercogs.APIManager")


class APIManager(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        self.headers: Mapping = {}
        self.cog_is_ready: asyncio.Event = asyncio.Event()
        self.start_up_task: asyncio.Task = asyncio.create_task(self.init())

    async def init(self):
        await self.bot.wait_until_red_ready()
        self.headers = {
            "Authorization": (await self.bot.get_shared_api_tokens("audiodb")).get("api_key")
        }
        self.cog_is_ready.set()

    @commands.group(name="audioapi")
    @commands.guild_only()
    async def command_audio_api(self, ctx: commands.Context):
        """Access to the Audio API command."""

    @command_audio_api.command(name="showinfo")
    @commands.guild_only()
    async def command_showinfo(
        self, ctx: commands.Context, *, user: Optional[Union[discord.User, int]] = None
    ):
        """Show user info."""
        if not await is_api_user(ctx):
            return

        if user is not None:
            user_id = user.id if isinstance(user, discord.abc.User) else user
            user = await API.get_user(cog=self, member=discord.Object(id=user_id))
        else:
            user = ctx.audio_api_user

        if user:
            new_data = {
                "Name": f"[{user.name}]",
                "User ID": f"[{user.user_id}]",
                "Entries Submitted": f"[{user.entries_submitted}]",
                "Can Read": f"[{user.can_read}]",
                "Can Post": f"[{user.can_post}]",
                "Can Delete": f"[{user.can_delete}]",
            }
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

    @command_audio_api.command(name="mytoken")
    @commands.guild_only()
    async def command_mytoken(self, ctx: commands.Context):
        """Get your user Global API details."""
        if not await is_api_user(ctx):
            return
        api_requester = ctx.audio_api_user
        if not api_requester:
            return await ctx.send("You aren't registered with the API.")
        if int(api_requester.user_id) != ctx.author.id:
            return await ctx.send("Failed to get user info")

        if api_requester.token is not None and not api_requester.is_blacklisted:
            await ctx.author.send(
                f"Use: `{ctx.clean_prefix}set api audiodb api_key {api_requester.token}` to set this key on your bot."
            )
        try:
            new_data = {
                "Name": f"[{api_requester.name}]",
                "User ID": f"[{api_requester.user_id}]",
                "Entries Submitted": f"[{api_requester.entries_submitted}]",
                "Can Read": f"[{api_requester.can_read}]",
                "Can Post": f"[{api_requester.can_post}]",
                "Can Delete": f"[{api_requester.can_delete}]",
            }

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
            if api_requester.token is not None:
                await ctx.author.send(
                    f"Use: `{ctx.clean_prefix}set api audiodb api_key {api_requester.token}` to set this key on your bot."
                )
        except discord.HTTPException:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("I can't DM you.")

    @command_audio_api.command(name="lb")
    @commands.guild_only()
    async def command_apilb(self, ctx: commands.Context):
        """Show the API Leaderboard."""
        if not await is_api_user(ctx):
            return
        users = await API.get_all_users(cog=self)
        if not users:
            return await ctx.send("Nothing found")
        data = [
            (u.entries_submitted, int(u.user_id), u.name)
            for u in users
            if ((not u.is_blacklisted) and u.token)
        ]
        data.sort(key=lambda x: x[0], reverse=True)
        await SimpleHybridMenu(
            source=LeaderboardSource(data),
            delete_message_after=True,
            timeout=60,
            clear_reactions_after=True,
        ).start(ctx)

    @command_audio_api.command(name="ban", cooldown_after_parsing=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def command_apiban(self, ctx: commands.Context, *, user: Union[discord.User, int]):
        """Ban people from server and API."""
        if not await is_api_admin(ctx):
            return
        api_requester = ctx.audio_api_user
        if not await self.is_allowed_by_hierarchy(api_requester, user):
            return await ctx.send("I can't allow you to do that.")

        if isinstance(user, discord.abc.User):
            user_name = str(user)
        else:
            try:
                user = await self.bot.fetch_user(user)
                user_name = str(user)
            except discord.HTTPException:
                user = discord.Object(id=user)
                user_name = "Deleted User"

        banned_user = await API.ban_user(cog=self, member=user, user_name=user_name)
        if not banned_user:
            return await ctx.send("I couldn't ban the user.")
        else:
            return await ctx.send(f"I have banned `{banned_user.name} ({banned_user.user_id})`.")

    @command_audio_api.command(name="massban", cooldown_after_parsing=True)
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def command_mass_apiban(self, ctx: commands.Context, *users: int):
        """Ban multiple people from server and API."""
        if not await is_api_admin(ctx):
            return
        await API.mass_ban_user(cog=self, users=list(users), user_name="Mass Banned")
        await ctx.tick()

    @command_audio_api.command(name="revoke")
    @commands.guild_only()
    async def command_apirevoke(self, ctx: commands.Context, *, user: Union[discord.User, int]):
        """Revoke people's API access."""
        if not await is_api_mod(ctx):
            return
        api_requester = ctx.audio_api_user
        if not await self.is_allowed_by_hierarchy(api_requester, user):
            return await ctx.send("I can't allow you to do that.")
        if isinstance(user, discord.abc.User):
            user_name = str(user)
        else:
            try:
                user = await self.bot.fetch_user(user)
                user_name = str(user)
            except discord.HTTPException:
                user = discord.Object(id=user)
                user_name = "Deleted User"
        revoked_user = await API.ban_user(cog=self, member=user, user_name=user_name)
        if not revoked_user:
            return await ctx.send("I couldn't revoke the user's token.")
        else:
            return await ctx.send(
                f"I have revoked `{revoked_user.name} ({revoked_user.user_id})` token."
            )

    @command_audio_api.command(name="contributor")
    @commands.guild_only()
    async def command_apicontributor(self, ctx: commands.Context, user_id: int):
        """Elevate a user to contributor status."""
        if not await is_api_mod(ctx):
            return
        api_requester = ctx.audio_api_user
        if not await self.is_allowed_by_hierarchy(api_requester, user_id, strict=True):
            return await ctx.send("I can't allow you to do that.")
        api_user = await API.update_user(cog=self, member=discord.Object(id=user_id), contrib=True)
        if not api_user:
            return await ctx.send(f"Couldn't update user `{user_id}` at this time.")
        await ctx.send(f"`{api_user.name} ({api_user.user_id})` is now a contributor.")

    @command_audio_api.command(name="mod")
    @commands.guild_only()
    async def command_apimod(self, ctx: commands.Context, user_id: int):
        """Elevate a user to mod status."""
        if not await is_api_admin(ctx):
            return
        api_requester = ctx.audio_api_user
        if not await self.is_allowed_by_hierarchy(api_requester, user_id, strict=True):
            return await ctx.send("I can't allow you to do that.")
        api_user = await API.update_user(cog=self, member=discord.Object(id=user_id), contrib=True)
        if not api_user:
            return await ctx.send(f"Couldn't update user `{user_id}` at this time.")
        await ctx.send(f"`{api_user.name} ({api_user.user_id})` is now a moderator.")

    @command_audio_api.command(name="register")
    @commands.guild_only()
    async def command_apiregister(self, ctx: commands.Context):
        """Register yourself with the Audio API."""
        if not await is_not_api_user(ctx):
            return
        api_user = await API.create_user(cog=self, member=ctx.author)
        if not api_user:
            return await ctx.send(
                f"Couldn't register {ctx.author} with the API, please try again later."
            )
        ctx.audio_api_user = api_user
        await ctx.invoke(self.command_mytoken)

    async def is_allowed_by_hierarchy(
        self, mod: User, user: Union[discord.abc.User, discord.Object, int], strict: bool = False
    ):
        if isinstance(user, (discord.abc.User, discord.Object)):
            user_id = user.id
        else:
            user_id = user
        user = await API.get_user(cog=self, member=discord.Object(id=user_id))
        if not user:
            return not strict
        if user.is_admin or user.is_superuser:
            return False
        if not strict:
            if mod.is_admin and any(
                s for s in [user.is_mod, user.is_contributor, user.is_user, user.is_guest]
            ):
                return True
            if mod.is_mod and any(s for s in [user.is_contributor, user.is_user, user.is_guest]):
                return True
        else:
            if mod.is_admin and any(s for s in [user.is_contributor, user.is_user, user.is_guest]):
                return True
            if mod.is_mod and any(s for s in [user.is_user, user.is_guest]):
                return True
        return False
