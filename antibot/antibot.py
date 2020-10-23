# -*- coding: utf-8 -*-
import contextlib
import logging

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, Union, Mapping

import aiohttp
import discord

from redbot.core import Config, commands
from redbot.core.utils.mod import get_audit_reason, is_allowed_by_hierarchy

from .converters import ConvertUserAPI

try:
    import regex
except Exception as e:
    raise RuntimeError(f"Can't load regex: {e}\nDo 'python -m pip install regex'.")

log = logging.getLogger("red.cogs.AntiBot")

discord_base_avatar_re = regex.compile(
    r"discordapp\.com\/embed\/avatars\/\d+", regex.IGNORECASE
)
discord_name_re = regex.compile(
    r"^\p{Letter}+\p{Number}+$|"
    r"^(\p{Letter}+\.)+(\p{Letter}+\p{Number}?)?$|"
    r"^\p{Letter}+[a-f\p{Number}]{3,4}$"
)

_default_guild = {
    "automod": False,
    "spammy_invite_links": {},
    "bypass_invite_links": {},
    "blacklist": [],
    "whitelist": [],
    "daythreshold": 7,
    "appealinvite": False,
}

extendedmodlog = None
modlog = None
_ = lambda s: s


class AntiBot(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        self.bot = bot
        self.config = Config.get_conf(
            self, identifier=8475527184, force_registration=True
        )
        self.config.register_guild(**_default_guild)
        self.session = aiohttp.ClientSession()
        self.ban_api = {}
        self.ban_queue: List[Tuple[int, int]] = []
        self.kick_queue: List[Tuple[int, int]] = []

    @commands.Cog.listener()
    async def on_red_api_tokens_update(
        self, service_name: str, api_tokens: Mapping[str, str]
    ) -> None:
        if service_name == "ksoft":
            self.ban_api = api_tokens

    async def initialize(self):
        self.ban_api = await self.bot.get_shared_api_tokens("ksoft")

    def cog_unload(self):
        if self.session:
            self.session.detach()

    @commands.admin_or_permissions(kick_members=True, ban_members=True)
    @commands.group(name="automod")
    async def _automod(self, ctx: commands.Context):
        """Toggles whether to auto ban new joins if they exist in the global database."""

    @commands.admin()
    @_automod.command()
    async def toggle(self, ctx: commands.Context, enabled: bool = None):
        """Toggles auto moderation on member joins."""
        if enabled is None:
            enabled = not await self.config.guild(ctx.guild).automod()
        await self.config.guild(ctx.guild).automod.set(enabled)
        await ctx.maybe_send_embed(
            _("Auto mod is: {status}").format(
                status=_("enabled") if enabled else _("disabled")
            )
        )

    @commands.admin()
    @_automod.command()
    async def days(self, ctx: commands.Context, days: int = None):
        """Set how many days an account needs to be before ignoring auto moderation."""
        if days < 1:
            days = 0
        await self.config.guild(ctx.guild).daythreshold.set(days)
        await ctx.maybe_send_embed(
            _("Accounts older than {days} will bypass auto moderation").format(
                days=days
            )
        )

    @commands.admin()
    @_automod.command()
    async def appeal(self, ctx: commands.Context, invite: str = None):
        """Sets an invite link to a secondary server (appeal server)"""
        await self.config.guild(ctx.guild).appealinvite.set(invite)
        if invite:
            await ctx.maybe_send_embed(
                _(
                    "On auto moderation I will now send users `{invite}` so they can appeal"
                ).format(invite=invite)
            )
        else:
            await ctx.maybe_send_embed(
                _("I'll silently auto moderate with no option to appeal")
            )

    @_automod.command()
    async def whitelist(
        self, ctx: commands.Context, user: Union[ConvertUserAPI, discord.Member] = None
    ):
        """Whitelist users to bypass automation check."""
        if user is None:
            return await ctx.send_help()

        guild = ctx.guild
        async with self.config.guild(guild).whitelist() as data:
            if user.id not in data:
                data.append(user.id)
                await ctx.maybe_send_embed(
                    _("{user} ({user.id}) will bypass the automation check").format(
                        user=user
                    )
                )
            else:
                data.remove(user.id)
                await ctx.maybe_send_embed(
                    _(
                        "{user} ({user.id}) will be checked on new joins by the automated system"
                    ).format(user=user)
                )

    @_automod.command()
    async def blacklist(
        self, ctx: commands.Context, user: Union[ConvertUserAPI, discord.Member] = None
    ):
        """Blacklist users to always kick on join."""
        if user is None:
            return await ctx.send_help()

        guild = ctx.guild
        async with self.config.guild(guild).blacklist() as data:
            if user.id not in data:
                data.append(user.id)
                await ctx.maybe_send_embed(
                    _("{user} ({user.id}) will always be kicked on rejoin").format(
                        user=user
                    )
                )
            else:
                data.remove(user.id)
                await ctx.maybe_send_embed(
                    _(
                        "{user} ({user.id}) will be checked on new joins by the automated system"
                    ).format(user=user)
                )

    @commands.admin()
    @_automod.command()
    async def recursive(self, ctx: commands.Context):
        """Go through member list and kick likely bots."""
        days = await self.config.guild(ctx.guild).daythreshold()
        allowed = datetime.utcnow() + timedelta(days=days)
        member_list = [m for m in ctx.guild.members if m.created_at < allowed]
        async with ctx.typing():
            for member in member_list:
                await self._auto_kick(member)
        await ctx.tick()

    @commands.admin()
    @_automod.command()
    async def bottyinvites(self, ctx: commands.Context, *invites):
        """Add invite links that most bots come from This makes users who join with this invite
        more likely to be kicked."""
        extendedmodlog = self.bot.get_cog("ExtendedModLog")
        if extendedmodlog is None:
            return await ctx.maybe_send_embed(
                _("You need the `{dep}`cog for this to work").format(
                    dep="ExtendedModLog"
                )
            )
        added = []
        removed = []
        async with self.config.guild(ctx.guild).spammy_invite_links() as spammy_invites:
            for i in invites:
                if i not in spammy_invites:
                    spammy_invites.update(i)
                    added.append(i)
                else:
                    spammy_invites.remove(i)
                    removed.append(i)
        if added:
            added = "\n".join(added)
            await ctx.maybe_send_embed(
                _("I've marked the following invites as spammy:\n\n{invs}").format(
                    invs=added
                )
            )
        if added:
            removed = "\n".join(removed)
            await ctx.maybe_send_embed(
                _("I've marked the following invites as not spammy:\n\n{invs}").format(
                    invs=removed
                )
            )

    @commands.admin()
    @_automod.command()
    async def bypassinvites(self, ctx: commands.Context, *invites):
        """Add invite links that allows users to bypass auto moderation."""
        extendedmodlog = self.bot.get_cog("ExtendedModLog")
        if extendedmodlog is None:
            return await ctx.maybe_send_embed(
                _("You need the `{dep}` cog for this to work").format(
                    dep="ExtendedModLog"
                )
            )
        added = []
        removed = []
        async with self.config.guild(ctx.guild).bypass_invite_links() as spammy_invites:
            for i in invites:
                if i not in spammy_invites:
                    spammy_invites.update(i)
                    added.append(i)
                else:
                    spammy_invites.remove(i)
                    removed.append(i)
        if added:
            added = "\n".join(added)
            await ctx.maybe_send_embed(
                _("The following links will bypass auto moderation:\n\n{invs}").format(
                    invs=removed
                )
            )
        if added:
            removed = "\n".join(removed)
            await ctx.maybe_send_embed(
                _(
                    "The following links will no longer bypass auto moderation:\n\n{invs}"
                ).format(invs=removed)
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if await self.auto_ban(member) is not True:
            self.bot.dispatch("new_member_join", member)

    async def auto_ban(self, member: discord.Member) -> Optional[bool]:
        guild = member.guild
        whitelist = await self.config.guild(guild).whitelist()
        if member.id in whitelist:
            log.info(
                f"{member} has been added to guild whitelist skipping automated checks"
            )
            return
        toggle = await self.config.guild(guild).autoban()
        ban = False
        reason = None
        if not toggle:
            return
        if not ban:
            try:
                log.info("Checking KSoft for bans")
                final = await self.ksoft_lookup(member)
            except ValueError:
                pass
            else:
                active_ban = final.get("is_ban_active")
                if active_ban:
                    log.info("Ban in KSoft found")
                    reason = final.get("reason")
                    ban = True

        if ban:
            log.info(f"Banning {member}")
            return await self.ban_sync(member, guild=guild, reason=reason)
        else:
            log.info(f"Checking for possible ban {member}")
            return await self._auto_kick(member)

    async def ksoft_lookup(self, user: discord.Member) -> dict:
        if self.ban_api["api_key"]:
            async with self.session.get(
                "https://api.ksoft.si/bans/info",
                params={"user": user.id},
                headers={"Authorization": self.ban_api["api_key"]},
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    return {}
        return {}

    async def _auto_kick(self, member: discord.Member) -> Optional[bool]:
        global extendedmodlog
        days = await self.config.guild(member.guild).daythreshold()
        now = datetime.utcnow()
        kicked = False
        real = 100
        blacklist = await self.config.guild(member.guild).blacklist()
        appeal = await self.config.guild(member.guild).appealinvite()
        bypass_invite = await self.config.guild(member.guild).bypass_invite_links()
        botty_invites = await self.config.guild(member.guild).spammy_invite_links()
        if member.id in blacklist:
            log.info(f"{member} has been added to guild blacklist force kicking")
            real -= 1000
        elif (
            member.is_avatar_animated()
            or member.activity
            or [a for a in member.activities if a]
            or now > member.created_at + timedelta(days=days)
        ):
            log.info(f"{member} passed kick check will not be kicked ...")
            return
        name = member.name
        guild = member.guild
        if extendedmodlog is None:
            extendedmodlog = self.bot.get_cog("ExtendedModLog")
        if extendedmodlog:
            invite = await extendedmodlog.get_invite_link(guild)
            invite = invite.split("\nInvited by: ")[0]
        else:
            invite = None
        if invite:
            if invite in bypass_invite and member.id not in blacklist:
                log.info(f"{member} passed kick check will not be kicked ...")
                return

        avatar = member.avatar_url_as(static_format="png")

        ban = 0
        diff = now - member.created_at
        diff = diff.days

        real -= (16 - diff) * 3

        if regex.search(discord_name_re, name, concurrent=True):
            ban += 20

        if regex.search(discord_base_avatar_re, str(avatar), concurrent=True):
            ban += 20

        if invite:
            if invite in botty_invites:
                ban += 35

        real -= ban
        if real <= 60:
            kicked = True
            queue_entry = (guild.id, member.id)
            if queue_entry in self.kick_queue:
                while queue_entry in self.kick_queue:
                    self.kick_queue.remove(queue_entry)
            if queue_entry not in self.kick_queue:
                if appeal:
                    await self.send_appeal_info(
                        member, guild, "kick", invite=appeal, is_auto=True
                    )
                # noinspection PyTypeChecker
                await self.kick_user(
                    member,
                    ctx=None,
                    reason="Auto removed likely bot account"
                    if member.id not in blacklist
                    else "Forced Kick: User has been added to blacklist",
                    create_modlog_case=True,
                    author=guild.me,
                    time=member.created_at,
                    guild=guild,
                    auto=True,
                )

            if queue_entry in self.kick_queue:
                while queue_entry in self.kick_queue:
                    self.kick_queue.remove(queue_entry)
        if kicked:
            log.info(f"Kicking {member}")
            return True

    @staticmethod
    async def send_appeal_info(
        user, guild, action, invite, is_auto=False, reason=None
    ) -> None:
        with contextlib.suppress(discord.HTTPException, discord.Forbidden):
            # We don't want blocked DMs preventing us from banning/kicking
            if is_auto:
                await user.send(
                    _(
                        "You have been kicked from {guild.name} "
                        "by our automation under suspicion of being a bot\n"
                        "If you are reading this you are not one"
                        "\nPlease join our appeal server and DM one of the Staff "
                        "who can get you in the server\nSorry for the inconvenience caused"
                    ).format(guild=guild)
                )
            else:
                if action == "ban":
                    action = _("banned")
                elif action == "kick":
                    action = _("kicked")
                if reason is None:
                    reason = ""
                else:
                    reason = _("Reason: {reason}").format(reason=reason)
                await user.send(
                    _("You have been {action} from {guild.name}. {reason}").format(
                        reason=reason, action=action, guild=guild
                    )
                )
            await user.send(
                _("Here is an invite to the appeal server: {invite}").format(
                    invite=invite
                )
            )

    async def kick_user(
        self,
        user: discord.Member,
        ctx: commands.Context,
        reason: str = None,
        create_modlog_case=False,
        type=None,
        author=None,
        time=None,
        guild=None,
        auto=False,
    ) -> Union[str, bool]:
        author = author or ctx.author
        guild = guild or ctx.guild

        global modlog
        if modlog is None:
            modlog = self.bot.get_cog("ModLog")

        if author == user:
            return "I cannot let you do that. Self-harm is bad \N{PENSIVE FACE}"
        elif not await is_allowed_by_hierarchy(
            self.bot, self.config, guild, author, user
        ):
            return (
                "I cannot let you do that. You are "
                "not higher than the user in the role "
                "hierarchy."
            )
        elif guild.me.top_role <= user.top_role or user == guild.owner:
            return "I cannot do that due to discord hierarchy rules"

        audit_reason = get_audit_reason(author, reason)
        appeal = await self.config.guild(guild).appealinvite()
        queue_entry = (guild.id, user.id)
        if queue_entry not in self.kick_queue:
            self.kick_queue.append(queue_entry)
        try:
            if not auto and appeal:
                await self.send_appeal_info(
                    user, guild, "kick", invite=appeal, is_auto=False, reason=reason
                )
            await guild.kick(user, reason=audit_reason)
            # TODO: Add permission check
            log.info(f"{author.name}({author.id}) kicked {user.name}({user.id})")
        except discord.Forbidden:
            if queue_entry in self.kick_queue:
                while queue_entry in self.kick_queue:
                    self.kick_queue.remove(queue_entry)
            return "I'm not allowed to do that."
        except Exception as err:
            if queue_entry in self.kick_queue:
                while queue_entry in self.kick_queue:
                    self.kick_queue.remove(queue_entry)
            return str(err)
        else:
            if queue_entry in self.kick_queue:
                while queue_entry in self.kick_queue:
                    self.kick_queue.remove(queue_entry)

        if create_modlog_case:
            try:
                if modlog:
                    await modlog.create_case(
                        self.bot,
                        guild,
                        time or ctx.message.created_at,
                        type or "kick",
                        user,
                        author,
                        reason,
                        until=None,
                        channel=None,
                    )
            except RuntimeError as err:
                return (
                    "The user was kicked but an error occurred when trying to "
                    f"create the modlog entry: {err}"
                )

        return True

    async def ban_sync(
        self, user: discord.Member, guild: discord.Guild, reason: str = None
    ) -> Union[str, bool]:
        global modlog
        if modlog is None:
            modlog = self.bot.get_cog("ModLog")
        author = guild.me

        if author == user:
            return "I cannot let you do that. Self-harm is bad \N{PENSIVE FACE}"
        elif not await is_allowed_by_hierarchy(
            self.bot, self.config, guild, author, user
        ):
            return (
                "I cannot let you do that. You are "
                "not higher than the user in the role "
                "hierarchy."
            )
        elif author.top_role <= user.top_role or user == guild.owner:
            return "I cannot do that due to discord hierarchy rules"

        now = datetime.now(timezone.utc)
        audit_reason = get_audit_reason(author, reason)
        queue_entry = (guild.id, user.id)
        self.ban_queue.append(queue_entry)
        appeal = await self.config.guild(guild).appealinvite()
        try:
            if appeal:
                await self.send_appeal_info(
                    user, guild, "ban", invite=appeal, is_auto=False, reason=reason
                )
            await guild.ban(user, reason=audit_reason, delete_message_days=1)
            # TODO: Add permission check
            log.info(
                f"{author.name}({author.id}) banned {user.name}({user.id}), "
                f"deleting {str(1)}  days worth of messages"
            )
        except discord.Forbidden:
            self.ban_queue.remove(queue_entry)
            return "I'm not allowed to do that."
        except Exception as err:
            self.ban_queue.remove(queue_entry)
            return str(err)

        try:
            if modlog:
                await modlog.create_case(
                    self.bot,
                    guild,
                    now,
                    "ban",
                    user,
                    author,
                    reason,
                    until=None,
                    channel=None,
                )
        except RuntimeError as err:
            return (
                "The user was banned but an error occurred when trying to "
                f"create the modlog entry: {err}"
            )

        return True
