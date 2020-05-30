# -*- coding: utf-8 -*-
# Standard Library
from typing import Mapping

# Cog Dependencies
from redbot.core import commands

# Cog Relative Imports
from ..classes.playlists import PlaylistScope
from ..utilities import _


class PlaylistConverter(commands.Converter):
    async def convert(self, ctx: commands.Context, arg: str) -> Mapping:
        """Get playlist for all scopes that match the argument user provided."""
        user_matches = []
        guild_matches = []
        global_matches = []
        if cog := ctx.cog:
            global_matches = await get_all_playlist_converter(
                PlaylistScope.GLOBAL.value,
                ctx.bot,
                cog.playlist_api,
                arg,
                guild=ctx.guild,
                author=ctx.author,
            )
            guild_matches = await get_all_playlist_converter(
                PlaylistScope.GUILD.value,
                ctx.bot,
                cog.playlist_api,
                arg,
                guild=ctx.guild,
                author=ctx.author,
            )
            user_matches = await get_all_playlist_converter(
                PlaylistScope.USER.value,
                ctx.bot,
                cog.playlist_api,
                arg,
                guild=ctx.guild,
                author=ctx.author,
            )
        if not user_matches and not guild_matches and not global_matches:
            raise commands.BadArgument(_("Could not match '{}' to a playlist.").format(arg))
        return {
            PlaylistScope.GLOBAL.value: global_matches,
            PlaylistScope.GUILD.value: guild_matches,
            PlaylistScope.USER.value: user_matches,
            "all": [*global_matches, *guild_matches, *user_matches],
            "arg": arg,
        }
