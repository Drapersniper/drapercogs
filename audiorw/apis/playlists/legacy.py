# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
from typing import List, MutableMapping, Optional, Union

# Cog Dependencies
import discord

from redbot.core.bot import Red

# Cog Relative Imports
from ...utilities.playlists import prepare_config_scope, standardize_scope
from . import PlaylistWrapper


class PlaylistCompat23:
    """A single playlist, migrating from Schema 2 to Schema 3."""

    def __init__(
        self,
        bot: Red,
        playlist_api: PlaylistWrapper,
        scope: str,
        author: int,
        playlist_id: int,
        name: str,
        playlist_url: Optional[str] = None,
        tracks: Optional[List[MutableMapping]] = None,
        guild: Union[discord.Guild, int, None] = None,
    ) -> None:

        self.bot = bot
        self.guild = guild
        self.scope = standardize_scope(scope)
        self.author = author
        self.id = playlist_id
        self.name = name
        self.url = playlist_url
        self.tracks = tracks or []

        self.playlist_api = playlist_api

    @classmethod
    async def from_json(
        cls,
        bot: Red,
        playlist_api: PlaylistWrapper,
        scope: str,
        playlist_number: int,
        data: MutableMapping,
        **kwargs,
    ) -> PlaylistCompat23:
        """Get a Playlist object from the provided information.
        Parameters
        ----------
        bot: Red
            The Bot instance.
        playlist_api: PlaylistWrapper
            The Playlist API interface.
        scope:str
            The custom config scope. One of 'GLOBALPLAYLIST', 'GUILDPLAYLIST' or 'USERPLAYLIST'.
        playlist_number: int
            The playlist's number.
        data: MutableMapping
            The JSON representation of the playlist to be gotten.
        **kwargs
            Extra attributes for the Playlist instance which override values
            in the data dict. These should be complete objects and not
            IDs, where possible.
        Returns
        -------
        Playlist
            The playlist object for the requested playlist.
        Raises
        ------
        `InvalidPlaylistScope`
            Passing a scope that is not supported.
        `MissingGuild`
            Trying to access the Guild scope without a guild.
        `MissingAuthor`
            Trying to access the User scope without an user id.
        """
        guild = data.get("guild") or kwargs.get("guild")
        author: int = data.get("author") or 0
        playlist_id = data.get("id") or playlist_number
        name = data.get("name", "Unnamed")
        playlist_url = data.get("playlist_url", None)
        tracks = data.get("tracks", [])

        return cls(
            bot=bot,
            playlist_api=playlist_api,
            guild=guild,
            scope=scope,
            author=author,
            playlist_id=playlist_id,
            name=name,
            playlist_url=playlist_url,
            tracks=tracks,
        )

    async def save(self) -> None:
        """Saves a Playlist to SQL."""
        scope, scope_id = prepare_config_scope(self.bot, self.scope, self.author, self.guild)
        await self.playlist_api.upsert(
            scope,
            playlist_id=int(self.id),
            playlist_name=self.name,
            scope_id=scope_id,
            author_id=self.author,
            playlist_url=self.url,
            tracks=self.tracks,
        )
