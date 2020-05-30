# -*- coding: utf-8 -*-
# Standard Library
from collections import namedtuple
from typing import Optional, Tuple, Union

# Cog Dependencies
import discord

from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list

# Cog Relative Imports
from .. import errors
from ..classes.playlists import PlaylistScope

__all__ = {
    "standardize_scope",
    "prepare_config_scope",
    "prepare_config_scope_for_migration23",
    "FakePlaylist",
}


def standardize_scope(scope: str) -> str:
    """Convert any of the used scopes into one we are expecting."""
    scope = scope.upper()
    valid_scopes = ["GLOBAL", "GUILD", "AUTHOR", "USER", "SERVER", "MEMBER", "BOT"]

    if scope in PlaylistScope.list():
        return scope
    elif scope not in valid_scopes:
        raise errors.InvalidPlaylistScope(
            f'"{scope}" is not a valid playlist scope.'
            f" Scope needs to be one of the following: {humanize_list(valid_scopes)}"
        )
    if scope in ["GLOBAL", "BOT"]:
        scope = PlaylistScope.GLOBAL.value
    elif scope in ["GUILD", "SERVER"]:
        scope = PlaylistScope.GUILD.value
    elif scope in ["USER", "MEMBER", "AUTHOR"]:
        scope = PlaylistScope.USER.value

    return scope


def prepare_config_scope(
    bot: Red,
    scope: str,
    author: Optional[Union[discord.abc.User, int]] = None,
    guild: Optional[Union[discord.Guild, int]] = None,
) -> Tuple[str, int]:
    """Return the scope used by Playlists."""
    scope = standardize_scope(scope)
    if scope == PlaylistScope.GLOBAL.value:
        config_scope = (PlaylistScope.GLOBAL.value, bot.user.id)
    elif scope == PlaylistScope.USER.value:
        if author is None:
            raise errors.MissingAuthor("Invalid author for user scope.")
        config_scope = (PlaylistScope.USER.value, int(getattr(author, "id", author)))
    else:
        if guild is None:
            raise errors.MissingGuild("Invalid guild for guild scope.")
        config_scope = (PlaylistScope.GUILD.value, int(getattr(guild, "id", guild)))
    return config_scope


def prepare_config_scope_for_migration23(
    scope: str, author: Union[discord.abc.User, int] = None, guild: Optional[discord.Guild] = None
) -> Tuple[str, ...]:
    """Return the scope used by Playlists for Legacy Playlists."""
    scope = standardize_scope(scope)

    if scope == PlaylistScope.GLOBAL.value:
        config_scope = (PlaylistScope.GLOBAL.value,)
    elif scope == PlaylistScope.USER.value:
        if author is None:
            raise errors.MissingAuthor("Invalid author for user scope.")
        config_scope = (PlaylistScope.USER.value, str(getattr(author, "id", author)))
    else:
        if guild is None:
            raise errors.MissingGuild("Invalid guild for guild scope.")
        config_scope = (PlaylistScope.GUILD.value, str(getattr(guild, "id", guild)))
    return config_scope


FakePlaylist = namedtuple("Playlist", "author scope")
