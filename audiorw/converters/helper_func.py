# -*- coding: utf-8 -*-
# Standard Library
from typing import Optional, Union

# Cog Dependencies
import discord

from redbot.core import commands
from redbot.core.utils import AsyncIter

# Cog Relative Imports
from .. import errors
from ..utilities import _, regex


def maybe_get_object_id(arg: str) -> Optional[int]:
    if m := regex.MENTION.match(arg):
        return int(m.group(1))
    return None


async def global_unique_guild_finder(ctx: commands.Context, arg: str) -> discord.Guild:
    bot = ctx.bot

    if (_id := maybe_get_object_id(arg)) is not None:
        if (guild := bot.get_guild(_id)) is not None:
            assert isinstance(guild, discord.Guild)
            return guild

    maybe_matches = {}
    async for guild in AsyncIter(bot.guilds):
        assert isinstance(guild, discord.Guild)
        if guild.name == arg or str(guild) == arg:
            maybe_matches[guild.id] = guild

    if not maybe_matches:
        raise errors.NoMatchesFound(
            _(
                '"{arg}" was not found. It must be the ID or '
                "complete name of a server which the bot can see."
            ).format(arg=arg)
        )
    elif len(maybe_matches) == 1:
        maybe_matches = list(maybe_matches.values())
        return maybe_matches[0]
    else:
        raise errors.TooManyMatches(
            _(
                '"{arg}" does not refer to a unique server. '
                "Please use the ID for the server you're trying to specify."
            ).format(arg=arg)
        )


async def global_unique_user_finder(
    ctx: commands.Context, arg: str, guild: Optional[discord.Guild] = None
) -> Union[discord.User, discord.Member]:
    bot = ctx.bot
    guild = guild or ctx.guild

    if (_id := maybe_get_object_id(arg)) is not None:
        if (user := bot.get_user(_id)) is not None:
            assert isinstance(user, discord.User)
            return user

    maybe_matches = {}
    async for user in AsyncIter(bot.users):
        assert isinstance(user, discord.User)
        if user.name == arg or f"{user}" == arg:
            maybe_matches[user.id] = user

    if guild is not None:
        async for member in AsyncIter(guild.members):
            assert isinstance(member, discord.Member)
            if member.nick == arg and member.id not in maybe_matches:
                maybe_matches[member.id] = member

    if not maybe_matches:
        raise errors.NoMatchesFound(
            _(
                '"{arg}" was not found. It must be the ID or name or '
                "mention a user which the bot can see."
            ).format(arg=arg)
        )
    elif len(maybe_matches) == 1:
        maybe_matches = list(maybe_matches.values())
        return maybe_matches[0]
    else:
        raise errors.TooManyMatches(
            _(
                '"{arg}" does not refer to a unique server. '
                "Please use the ID for the server you're trying to specify."
            ).format(arg=arg)
        )
