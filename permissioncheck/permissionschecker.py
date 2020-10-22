import collections
import logging
import time

import discord
from discord.ext.commands import CheckFailure, CommandError
from redbot.core import Config, commands
from redbot.core.commands import Context
from redbot.core.utils.chat_formatting import box, pagify

_ = lambda s: s


HUMANIZED_PERM = {
    "create_instant_invite": "Create Instant Invite",
    "kick_members": "Kick Members",
    "ban_members": "Ban Members",
    "administrator": "Administrator",
    "manage_channels": "Manage Channels",
    "manage_guild": "Manage Server",
    "add_reactions": "Add Reactions",
    "view_audit_log": "View Audit Log",
    "priority_speaker": "Priority Speaker",
    "stream": "Go Live",
    "read_messages": "Read Text Channels & See Voice Channels",
    "send_messages": "Send Messages",
    "send_tts_messages": "Send TTS Messages",
    "manage_messages": "Manage Messages",
    "embed_links": "Embed Links",
    "attach_files": "Attach Files",
    "read_message_history": "Read Message History",
    "mention_everyone": "Mention @everyone, @here, and All Roles",
    "external_emojis": "Use External Emojis",
    "view_guild_insights": "View Server Insights",
    "connect": "Connect",
    "speak": "Speak",
    "mute_members": "Mute Members",
    "deafen_members": "Deafen Members",
    "move_members": "Move Members",
    "use_voice_activation": "Use Voice Activity",
    "change_nickname": "Change Nickname",
    "manage_nicknames": "Manage Nicknames",
    "manage_roles": "Manage Roles",
    "manage_webhooks": "Manage Webhooks",
    "manage_emojis": "Manage Emojis",
}

log = logging.getLogger("red.drapercogs.PermissionsChecker")


class PermissionsChecker(commands.Cog):
    """Permissions Checker commands."""

    def __init__(self, bot):
        self.bot = bot
        self.config: Config = Config.get_conf(self, 208903205982044161, force_registration=True)
        default_perms = {
            "send_messages": True,
            "read_messages": True,
            "add_reactions": True,
            "embed_links": True,
        }
        self.config.register_global(blacklist=[], permissions=default_perms)
        self.config.register_guild(error_count=0, last_error=0)
        self.permission_cache: discord.Permissions = None

    async def bot_check_once(self, ctx: Context):
        if ctx.guild and ctx.guild.id in [133049272517001216]:
            return True
        current_perms = ctx.channel.permissions_for(ctx.me)
        surpass_ignore = (
            isinstance(ctx.channel, discord.abc.PrivateChannel)
            or current_perms.manage_guild
            or await ctx.bot.is_owner(ctx.author)
            or await ctx.bot.is_admin(ctx.author)
        )
        if surpass_ignore:
            return True
        if self.permission_cache is None:
            self.permission_cache = discord.Permissions(**(await self.config.permissions.all()))
        guild = ctx.guild
        if guild and not current_perms.is_superset(self.permission_cache):
            current_perms_set = set(iter(current_perms))
            expected_perms_set = set(iter(self.permission_cache))
            diff = expected_perms_set - current_perms_set
            missing_perms = dict((i for i in diff if i[-1] is not False))
            missing_perms = collections.OrderedDict(sorted(missing_perms.items()))
            text = (
                "I'm missing permissions in this server, "
                "Please address this as soon as possible. "
                "If this continues I will leave the server.\n\n"
                "I need the following permissions which I currently lack:\n"
            )
            for perm, value in missing_perms.items():
                text += f"{HUMANIZED_PERM.get(perm)}: [{'On' if value else 'Off'}]\n"
            text = text.strip()
            if current_perms.send_messages and current_perms.read_messages:
                await ctx.send(box(text=text, lang="ini"))
            raise CheckFailure(message=text)
        return True

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: CommandError):
        if ctx.guild and ctx.guild.id in [133049272517001216]:
            return
        if await ctx.bot.is_owner(ctx.author):
            return
        error = getattr(error, "original", error)
        if self.permission_cache is None:
            self.permission_cache = discord.Permissions(**(await self.config.permissions.all()))
        if isinstance(error, (discord.HTTPException,)) and getattr(error, "code", None) in [
            50001,
            50013,
        ]:
            channel = ctx.channel
            guild = ctx.guild
            current_perms: discord.Permissions = ctx.me.permissions_in(channel)
            if guild and not current_perms.is_superset(self.permission_cache):
                current_perms_set = set(iter(current_perms))
                expected_perms_set = set(iter(self.permission_cache))
                diff = expected_perms_set - current_perms_set
                missing_perms = dict((i for i in diff if i[-1] is not False))
                missing_perms = collections.OrderedDict(sorted(missing_perms.items()))
                text = (
                    "I'm missing permissions in this server, "
                    "Please address this as soon as possible. "
                    "If this continues I will leave the server.\n\n"
                    "I need the following permissions which I currently lack:\n"
                )
                for perm, value in missing_perms.items():
                    text += f"{HUMANIZED_PERM.get(perm)}: [{'On' if value else 'Off'}]\n"
                text = text.strip()
                async with self.config.guild(guild).all() as channel_data:
                    if channel_data["last_error"] > time.time() + 600:
                        channel_data["error_count"] = 0
                    if channel_data["error_count"] >= 10:
                        del channel_data["last_error"]
                        del channel_data["error_count"]
                        await ctx.send(
                            "Too many permissions errors in this server, "
                            "you been warned 10 times, and didn't take action. "
                            "I will be leaving the server now"
                        )
                        async with self.config.blacklist() as blacklist:
                            if guild.id not in blacklist:
                                blacklist.append(guild.id)
                        return await guild.leave()
                    channel_data["last_error"] = time.time()
                    channel_data["error_count"] += 1
                if current_perms.send_messages and current_perms.read_messages:
                    await ctx.send(box(text=text, lang="ini"))
                return

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        async with self.config.blacklist() as blacklist:
            if any(x in blacklist for x in (guild.id, guild.owner.id)):
                log.info(f"leaving guild: {guild}({guild.id})")
                await guild.leave()

    @commands.is_owner()
    @commands.group(name="pchecker")
    async def pchecker(self, ctx: commands.Context):
        """Settings for Permission Checker."""

    @pchecker.command(name="permissions")
    async def pchecker_permissions(self, ctx: commands.Context, perms_int: int):
        """Set minimum required perms for the bot to work.

        You can generate one here: https://discordapi.com/permissions.html
        """
        permissions = discord.Permissions(perms_int)
        permissions = dict((i for i in iter(permissions) if i[-1] is True))
        await self.config.permissions.set(permissions)
        self.permission_cache = discord.Permissions(**permissions)
        text = "From now on I will expected the following permissions in a channel:\n\n"
        permissions = collections.OrderedDict(sorted(permissions.items()))
        for perm, value in permissions.items():
            text += f"{HUMANIZED_PERM.get(perm)}: [{'On' if value else 'Off'}]\n"
        text = text.strip()
        await ctx.send(box(text=text, lang="ini"))

    @pchecker.group(name="blacklist")
    async def pchecker_blacklist(self, ctx: commands.Context):
        """Settings for the server blacklist."""

    @pchecker_blacklist.command(name="list")
    async def pchecker_blacklist_list(self, ctx: commands.Context):
        """List all blacklisted server IDs."""
        blacklist = await self.config.blacklist()
        output = "\n".join(["IDs in blacklist:", *map(str, blacklist)])

        for page in pagify(output):
            await ctx.send(box(page))
        await ctx.tick()

    @pchecker_blacklist.command(name="remove")
    async def pchecker_blacklist_remove(self, ctx: commands.Context, *server_ids: int):
        """Remove one or more server IDs from the blacklist"""
        if not server_ids:
            return await ctx.send_help()

        async with self.config.blacklist() as blacklist:
            for server_id in server_ids:
                if server_id in blacklist:
                    blacklist.remove(server_id)
        await ctx.tick()
