# -*- coding: utf-8 -*-
# Standard Library
import argparse

from typing import Optional, Tuple, Union

# Cog Dependencies
import discord

from redbot.core import commands

# Cog Relative Imports
from .. import errors
from ..classes.playlists import PlaylistScope
from ..utilities import constants
from ..utilities.playlists import standardize_scope
from .helper_func import global_unique_guild_finder, global_unique_user_finder

__all__ = {"ScopeParser", "ComplexScopeParser"}


class NoExitParser(argparse.ArgumentParser):
    def error(self, message) -> None:
        raise commands.BadArgument()


class ScopeParser(commands.Converter):
    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> Tuple[Optional[str], discord.User, Optional[discord.Guild], bool]:

        target_scope: Optional[str] = None
        target_user: Optional[Union[discord.Member, discord.User]] = None
        target_guild: Optional[discord.Guild] = None
        specified_user = False

        argument = argument.replace("—", "--")

        command, *arguments = argument.split(" -- ")
        if arguments:
            argument = " -- ".join(arguments)
        else:
            command = ""

        parser = NoExitParser(description="Playlist Scope Parsing.", add_help=False)
        parser.add_argument("--scope", nargs="*", dest="scope", default=[])
        parser.add_argument("--guild", nargs="*", dest="guild", default=[])
        parser.add_argument("--server", nargs="*", dest="guild", default=[])
        parser.add_argument("--author", nargs="*", dest="author", default=[])
        parser.add_argument("--user", nargs="*", dest="author", default=[])
        parser.add_argument("--member", nargs="*", dest="author", default=[])

        if not command:
            parser.add_argument("command", nargs="*")

        try:
            vals = vars(parser.parse_args(argument.split()))
        except Exception as exc:
            raise commands.BadArgument() from exc

        if vals["scope"]:
            scope_raw = " ".join(vals["scope"]).strip()
            scope = scope_raw.upper().strip()
            valid_scopes = PlaylistScope.list() + [
                "GLOBAL",
                "GUILD",
                "AUTHOR",
                "USER",
                "SERVER",
                "MEMBER",
                "BOT",
            ]
            if scope not in valid_scopes:
                raise errors.ArgParserFailure(
                    "--scope", scope_raw, custom_help=constants.ARG_PARSER_SCOPE_HELP
                )
            target_scope = standardize_scope(scope)
        elif "--scope" in argument and not vals["scope"]:
            raise errors.ArgParserFailure(
                "--scope", "Nothing", custom_help=constants.ARG_PARSER_SCOPE_HELP
            )

        is_owner = await ctx.bot.is_owner(ctx.author)
        guild = vals.get("guild", None) or vals.get("server", None)
        if is_owner and guild:
            server_error = ""
            target_guild = None
            guild_raw = " ".join(guild).strip()
            try:
                target_guild = await global_unique_guild_finder(ctx, guild_raw)
            except errors.TooManyMatches as err:
                server_error = f"{err}\n"
            except errors.NoMatchesFound as err:
                server_error = f"{err}\n"
            if target_guild is None:
                raise errors.ArgParserFailure(
                    "--guild",
                    guild_raw,
                    custom_help=f"{server_error}{constants.ARG_PARSER_GUILD_HELP}",
                )

        elif not is_owner and (guild or any(x in argument for x in ["--guild", "--server"])):
            raise commands.BadArgument("You cannot use `--guild`")
        elif any(x in argument for x in ["--guild", "--server"]):
            raise errors.ArgParserFailure(
                "--guild", "Nothing", custom_help=constants.ARG_PARSER_GUILD_HELP
            )

        author = vals.get("author", None) or vals.get("user", None) or vals.get("member", None)
        if author:
            user_error = ""
            target_user = None
            user_raw = " ".join(author).strip()
            try:
                target_user = await global_unique_user_finder(ctx, user_raw, guild=target_guild)
                specified_user = True
            except errors.TooManyMatches as err:
                user_error = f"{err}\n"
            except errors.NoMatchesFound as err:
                user_error = f"{err}\n"

            if target_user is None:
                raise errors.ArgParserFailure(
                    "--author",
                    user_raw,
                    custom_help=f"{user_error}{constants.ARG_PARSER_USER_HELP}",
                )
        elif any(x in argument for x in ["--author", "--user", "--member"]):
            raise errors.ArgParserFailure(
                "--scope", "Nothing", custom_help=constants.ARG_PARSER_USER_HELP
            )

        target_scope: Optional[str] = target_scope or None
        target_user: Union[discord.Member, discord.User] = target_user or ctx.author
        target_guild: discord.Guild = target_guild or ctx.guild

        return target_scope, target_user, target_guild, specified_user


class ComplexScopeParser(commands.Converter):
    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> Tuple[
        str,
        discord.User,
        Optional[discord.Guild],
        bool,
        str,
        discord.User,
        Optional[discord.Guild],
        bool,
    ]:

        target_scope: Optional[str] = None
        target_user: Optional[Union[discord.Member, discord.User]] = None
        target_guild: Optional[discord.Guild] = None
        specified_target_user = False

        source_scope: Optional[str] = None
        source_user: Optional[Union[discord.Member, discord.User]] = None
        source_guild: Optional[discord.Guild] = None
        specified_source_user = False

        argument = argument.replace("—", "--")

        command, *arguments = argument.split(" -- ")
        if arguments:
            argument = " -- ".join(arguments)
        else:
            command = ""

        parser = NoExitParser(description="Playlist Scope Parsing.", add_help=False)

        parser.add_argument("--to-scope", nargs="*", dest="to_scope", default=[])
        parser.add_argument("--to-guild", nargs="*", dest="to_guild", default=[])
        parser.add_argument("--to-server", nargs="*", dest="to_server", default=[])
        parser.add_argument("--to-author", nargs="*", dest="to_author", default=[])
        parser.add_argument("--to-user", nargs="*", dest="to_user", default=[])
        parser.add_argument("--to-member", nargs="*", dest="to_member", default=[])

        parser.add_argument("--from-scope", nargs="*", dest="from_scope", default=[])
        parser.add_argument("--from-guild", nargs="*", dest="from_guild", default=[])
        parser.add_argument("--from-server", nargs="*", dest="from_server", default=[])
        parser.add_argument("--from-author", nargs="*", dest="from_author", default=[])
        parser.add_argument("--from-user", nargs="*", dest="from_user", default=[])
        parser.add_argument("--from-member", nargs="*", dest="from_member", default=[])

        if not command:
            parser.add_argument("command", nargs="*")

        try:
            vals = vars(parser.parse_args(argument.split()))
        except Exception as exc:
            raise commands.BadArgument() from exc

        is_owner = await ctx.bot.is_owner(ctx.author)
        valid_scopes = PlaylistScope.list() + [
            "GLOBAL",
            "GUILD",
            "AUTHOR",
            "USER",
            "SERVER",
            "MEMBER",
            "BOT",
        ]

        if vals["to_scope"]:
            to_scope_raw = " ".join(vals["to_scope"]).strip()
            to_scope = to_scope_raw.upper().strip()
            if to_scope not in valid_scopes:
                raise errors.ArgParserFailure(
                    "--to-scope", to_scope_raw, custom_help=constants.ARG_PARSER_SCOPE_HELP
                )
            target_scope = standardize_scope(to_scope)
        elif "--to-scope" in argument and not vals["to_scope"]:
            raise errors.ArgParserFailure(
                "--to-scope", "Nothing", custom_help=constants.ARG_PARSER_SCOPE_HELP
            )

        if vals["from_scope"]:
            from_scope_raw = " ".join(vals["from_scope"]).strip()
            from_scope = from_scope_raw.upper().strip()

            if from_scope not in valid_scopes:
                raise errors.ArgParserFailure(
                    "--from-scope", from_scope_raw, custom_help=constants.ARG_PARSER_USER_HELP
                )
            source_scope = standardize_scope(from_scope)
        elif "--from-scope" in argument and not vals["to_scope"]:
            raise errors.ArgParserFailure(
                "--to-scope", "Nothing", custom_help=constants.ARG_PARSER_SCOPE_HELP
            )

        to_guild = vals.get("to_guild", None) or vals.get("to_server", None)
        if is_owner and to_guild:
            target_server_error = ""
            target_guild = None
            to_guild_raw = " ".join(to_guild).strip()
            try:
                target_guild = await global_unique_guild_finder(ctx, to_guild_raw)
            except errors.TooManyMatches as err:
                target_server_error = f"{err}\n"
            except errors.NoMatchesFound as err:
                target_server_error = f"{err}\n"
            if target_guild is None:
                raise errors.ArgParserFailure(
                    "--to-guild",
                    to_guild_raw,
                    custom_help=f"{target_server_error}{constants.ARG_PARSER_GUILD_HELP}",
                )
        elif not is_owner and (
            to_guild or any(x in argument for x in ["--to-guild", "--to-server"])
        ):
            raise commands.BadArgument("You cannot use `--to-server`")
        elif any(x in argument for x in ["--to-guild", "--to-server"]):
            raise errors.ArgParserFailure(
                "--to-server", "Nothing", custom_help=constants.ARG_PARSER_GUILD_HELP
            )

        from_guild = vals.get("from_guild", None) or vals.get("from_server", None)
        if is_owner and from_guild:
            source_server_error = ""
            source_guild = None
            from_guild_raw = " ".join(from_guild).strip()
            try:
                source_guild = await global_unique_guild_finder(ctx, from_guild_raw)
            except errors.TooManyMatches as err:
                source_server_error = f"{err}\n"
            except errors.NoMatchesFound as err:
                source_server_error = f"{err}\n"
            if source_guild is None:
                raise errors.ArgParserFailure(
                    "--from-guild",
                    from_guild_raw,
                    custom_help=f"{source_server_error}{constants.ARG_PARSER_GUILD_HELP}",
                )
        elif not is_owner and (
            from_guild or any(x in argument for x in ["--from-guild", "--from-server"])
        ):
            raise commands.BadArgument("You cannot use `--from-server`")
        elif any(x in argument for x in ["--from-guild", "--from-server"]):
            raise errors.ArgParserFailure(
                "--from-server", "Nothing", custom_help=constants.ARG_PARSER_GUILD_HELP
            )

        to_author = (
            vals.get("to_author", None) or vals.get("to_user", None) or vals.get("to_member", None)
        )
        if to_author:
            target_user_error = ""
            target_user = None
            to_user_raw = " ".join(to_author).strip()
            try:
                target_user = await global_unique_user_finder(ctx, to_user_raw, guild=target_guild)
                specified_target_user = True
            except errors.TooManyMatches as err:
                target_user_error = f"{err}\n"
            except errors.NoMatchesFound as err:
                target_user_error = f"{err}\n"
            if target_user is None:
                raise errors.ArgParserFailure(
                    "--to-author",
                    to_user_raw,
                    custom_help=f"{target_user_error}{constants.ARG_PARSER_USER_HELP}",
                )
        elif any(x in argument for x in ["--to-author", "--to-user", "--to-member"]):
            raise errors.ArgParserFailure(
                "--to-user", "Nothing", custom_help=constants.ARG_PARSER_USER_HELP
            )

        from_author = (
            vals.get("from_author", None)
            or vals.get("from_user", None)
            or vals.get("from_member", None)
        )
        if from_author:
            source_user_error = ""
            source_user = None
            from_user_raw = " ".join(from_author).strip()
            try:
                source_user = await global_unique_user_finder(
                    ctx, from_user_raw, guild=target_guild
                )
                specified_target_user = True
            except errors.TooManyMatches as err:
                source_user_error = f"{err}\n"
            except errors.NoMatchesFound as err:
                source_user_error = f"{err}\n"
            if source_user is None:
                raise errors.ArgParserFailure(
                    "--from-author",
                    from_user_raw,
                    custom_help=f"{source_user_error}{constants.ARG_PARSER_USER_HELP}",
                )
        elif any(x in argument for x in ["--from-author", "--from-user", "--from-member"]):
            raise errors.ArgParserFailure(
                "--from-user", "Nothing", custom_help=constants.ARG_PARSER_USER_HELP
            )

        target_scope = target_scope or PlaylistScope.GUILD.value
        target_user = target_user or ctx.author
        target_guild = target_guild or ctx.guild

        source_scope = source_scope or PlaylistScope.GUILD.value
        source_user = source_user or ctx.author
        source_guild = source_guild or ctx.guild

        return (
            source_scope,
            source_user,
            source_guild,
            specified_source_user,
            target_scope,
            target_user,
            target_guild,
            specified_target_user,
        )
