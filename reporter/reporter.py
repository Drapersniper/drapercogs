# -*- coding: utf-8 -*-
import inspect

from collections import Counter
from copy import deepcopy
import discord

from redbot.core import Config, bank, commands, modlog
from redbot.core.i18n import Translator
from redbot.core.utils.chat_formatting import box, pagify

from .converter import ConvertUserAPI, GuildConverterAPI

_ = Translator("Reporter", __file__)


def predicate(attribute):
    return isinstance(attribute, Config)


class Reporter(commands.Cog):
    """Setting reporter."""

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def maybe_get_config(cog: commands.Cog):
        cog_name = (
            cog.qualified_name
            if hasattr(cog, "qualified_name")
            else cog.__class__.__name__
        )
        config_attribute = inspect.getmembers(cog, predicate)
        if cog_name == "Bank":
            return bank._conf
        elif cog_name == "ModLog":
            return modlog._conf
        elif config_attribute:
            return config_attribute[0][1]
        else:
            return None

    @staticmethod
    def get_usage(lists: list) -> str:
        count = Counter(lists).items()
        percentages = {x: int(float(y) / len(lists) * 100) for x, y in count}
        if len(percentages) > 5:
            return _("Too many values to show")
        data = ""
        for name, pct in percentages.items():
            data += f'<{name} - {pct}{"%"}> '
        return data

    @commands.is_owner()
    @commands.group(name="usagereport")
    async def _report(self, ctx: commands.Context):
        """Check bot settings."""

    @_report.group(name="global")
    async def _report_global(self, ctx: commands.Context):
        """Check global bot settings for the specified Cog."""

    @_report_global.command(name="guild")
    async def _report_global_guild(self, ctx: commands.Context, cog: str):
        """Check global guild bot settings for the specified Cog."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "Red":  # TODO wait for core fix
            config = self.bot._config
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        global_config = await config.all_guilds()
        temp = deepcopy(global_config)
        for k, v in temp.items():
            for gk, gv in v.items():
                if not isinstance(gv, (str, bool, int, type(None))) or "token" in gk:
                    del global_config[k][gk]
        new = {}
        for gid, gdata in global_config.items():
            for k, v in gdata.items():
                if k not in new:
                    new[k] = [v]
                else:
                    new[k].append(v)

        new2 = {}
        for k, v in new.items():
            new2[k] = self.get_usage(v)
        if not new2:
            return await ctx.send(
                _("No guild settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        max_len = max([len(v) for v in new2.keys()])
        padding = 4
        data = _("< {cog} > Guild settings for {bot.name}\n\n").format(
            bot=self.bot.user,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(new2.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = v
            data += "{k:{k_len:d}} | {v}\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))

    @_report_global.command(name="member")
    async def _report_global_member(self, ctx: commands.Context, cog: str):
        """Check global member bot settings for the specified Cog."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "nonono" "Red":  # TODO wait for core fix
            config = Config.get_core_conf(force_registration=False)
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        global_config = await config.all_members()
        temp = deepcopy(global_config)
        for gk, gv in temp.items():
            for mk, mv in gv.items():
                for k, v in mv.items():
                    if not isinstance(v, (str, bool, int, type(None))) or "token" in k:
                        del global_config[gk][mk][k]
        new = {}
        for gid, gdata in global_config.items():
            for mk, mv in gdata.items():
                for k, v in mv.items():
                    if k not in new:
                        new[k] = [v]
                    else:
                        new[k].append(v)
        new2 = {}
        for k, v in new.items():
            new2[k] = self.get_usage(v)

        if not new2:
            return await ctx.send(
                _("No member settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )

        max_len = max([len(v) for v in new2.keys()])
        padding = 4
        data = _("< {cog} > Member settings for {bot.name}\n\n").format(
            bot=self.bot.user,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(new2.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = v
            data += "{k:{k_len:d}} | {v}\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))

    @_report_global.command(name="user")
    async def _report_global_user(self, ctx: commands.Context, cog: str):
        """Check global member bot settings for the specified Cog."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "nonono" "Red":  # TODO wait for core fix
            config = Config.get_core_conf(force_registration=False)
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        global_config = await config.all_users()
        temp = deepcopy(global_config)
        for k, v in temp.items():
            for gk, gv in v.items():
                if not isinstance(gv, (str, bool, int, type(None))) or "token" in gk:
                    del global_config[k][gk]
        new = {}
        for gid, gdata in global_config.items():
            for k, v in gdata.items():
                if k not in new:
                    new[k] = [v]
                else:
                    new[k].append(v)
        new2 = {}
        for k, v in new.items():
            new2[k] = self.get_usage(v)
        if not new2:
            return await ctx.send(
                _("No user settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        max_len = max([len(v) for v in new2.keys()])
        padding = 4
        data = _("< {cog} > User settings for {bot.name}\n\n").format(
            bot=self.bot.user,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(new2.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = v
            data += "{k:{k_len:d}} | {v}\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))

    @_report.command(name="guild")
    async def _report_guild(
        self, ctx: commands.Context, cog: str, *, guild: GuildConverterAPI
    ):
        """Check guild bot settings for the specified Cog in the specified Guild."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "nonono" "Red":  # TODO wait for core fix
            config = Config.get_core_conf(force_registration=False)
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        guild_config = await config.guild(guild).all()
        temp = guild_config.copy()
        for k, v in temp.items():
            if not isinstance(v, (str, bool, int, type(None))) or "token" in k:
                del guild_config[k]

        max_len = max([len(v) for v in guild_config.keys()])
        padding = 4
        data = _("< {cog} > settings for {guild.name}\n\n").format(
            guild=guild,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(guild_config.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = str(v)
            data += "{k:{k_len:d}} | <{v}>\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))

    @_report.command(name="globals")
    async def _report_globals(self, ctx: commands.Context, cog: str):
        """Check bot settings for the specified Cog in the global scope."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "nonono" "Red":  # TODO wait for core fix
            config = Config.get_core_conf(force_registration=False)
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        global_config = await config.all()
        temp = global_config.copy()
        for k, v in temp.items():
            if not isinstance(v, (str, bool, int, type(None))) or "token" in k:
                del global_config[k]

        max_len = max([len(v) for v in global_config.keys()])
        padding = 4
        data = _("< {cog} > Settings for {bot.name}\n\n").format(
            bot=self.bot.user,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(global_config.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = str(v)
            data += "{k:{k_len:d}} | <{v}>\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))

    @_report.command(name="user")
    async def _report_user(self, ctx: commands.Context, cog: str, user: ConvertUserAPI):
        """Check bot settings for the specified Cog in the user scope."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "nonono" "Red":  # TODO wait for core fix
            config = Config.get_core_conf(force_registration=False)
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        user_config = await config.user(user).all()
        temp = user_config.copy()
        for k, v in temp.items():
            if not isinstance(v, (str, bool, int, type(None))) or "token" in k:
                del user_config[k]

        max_len = max([len(v) for v in user_config.keys()])
        padding = 4
        data = _("< {cog} > Settings for {user}\n\n").format(
            user=user,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(user_config.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = str(v)
            data += "{k:{k_len:d}} | <{v}>\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))

    @_report.command(name="member")
    async def _report_member(
        self, ctx: commands.Context, cog: str, member: discord.Member
    ):
        """Check bot settings for the specified Cog in the Member scope."""
        cog_obj = ctx.bot.get_cog(cog)
        if cog_obj is None and cog != "Red":
            return await ctx.send(
                _("Unable to find a cog called: {cog}").format(cog=cog)
            )
        elif cog == "nonono" "Red":  # TODO wait for core fix
            config = Config.get_core_conf(force_registration=False)
        else:
            config = self.maybe_get_config(cog_obj)
        if config is None:
            return await ctx.send(
                _("Unable to find settings for: {cog}").format(
                    cog=cog_obj.qualified_name
                    if hasattr(cog_obj, "qualified_name")
                    else cog_obj.__class__.__name__
                    if cog != "Red"
                    else "Red Core"
                )
            )
        member_config = await config.member(member).all()
        temp = member_config.copy()
        for k, v in temp.items():
            if not isinstance(v, (str, bool, int, type(None))) or "token" in k:
                del member_config[k]

        max_len = max([len(v) for v in member_config.keys()])
        padding = 4
        data = _("< {cog} > Settings for {user}\n\n").format(
            user=member,
            cog=cog_obj.qualified_name
            if hasattr(cog_obj, "qualified_name")
            else cog_obj.__class__.__name__
            if cog != "Red"
            else "Red Core",
        )
        for k, v in sorted(member_config.items(), key=lambda i: str(i[0])):
            k = str(k).replace("_", " ").title()
            v = str(v)
            data += "{k:{k_len:d}} | <{v}>\n".format(k_len=max_len + padding, v=v, k=k)
        for page in pagify(data, shorten_by=10):
            await ctx.send(box(page, lang="md"))
