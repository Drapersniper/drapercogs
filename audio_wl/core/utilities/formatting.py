# -*- coding: utf-8 -*-
# Standard Library
import datetime
import logging
import math
import re
import time

from typing import List

# Cog Dependencies
import discord
import wavelink

from discord.embeds import EmptyEmbed
from redbot.core import commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import box, escape

# Cog Relative Imports
from ...audio_dataclasses import LocalPath, Query
from ...audio_logging import IS_DEBUG
from ...wavelink_overrides import Player, PlayerStatus
from ..abc import MixinMeta
from ..cog_utils import CompositeMetaClass, _

log = logging.getLogger("red.cogs.Audio.cog.Utilities.formatting")

RE_SQUARE = re.compile(r"[\[\]]")


class FormattingUtilities(MixinMeta, metaclass=CompositeMetaClass):
    async def _genre_search_button_action(
        self, ctx: commands.Context, options: List, emoji: str, page: int, playlist: bool = False
    ) -> str:
        try:
            if emoji == "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = options[0 + (page * 5)]
            elif emoji == "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = options[1 + (page * 5)]
            elif emoji == "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = options[2 + (page * 5)]
            elif emoji == "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = options[3 + (page * 5)]
            elif emoji == "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = options[4 + (page * 5)]
            else:
                search_choice = options[0 + (page * 5)]
        except IndexError:
            search_choice = options[-1]
        if not playlist:
            return list(search_choice.items())[0]
        else:
            return search_choice.get("uri")

    async def _build_genre_search_page(
        self,
        ctx: commands.Context,
        tracks: List,
        page_num: int,
        title: str,
        playlist: bool = False,
    ) -> discord.Embed:
        search_num_pages = math.ceil(len(tracks) / 5)
        search_idx_start = (page_num - 1) * 5
        search_idx_end = search_idx_start + 5
        search_list = ""
        async for i, entry in AsyncIter(tracks[search_idx_start:search_idx_end]).enumerate(
            start=search_idx_start
        ):
            search_track_num = i + 1
            if search_track_num > 5:
                search_track_num = search_track_num % 5
            if search_track_num == 0:
                search_track_num = 5
            if playlist:
                name = "**[{}]({})** - {} {}".format(
                    entry.get("name"), entry.get("url"), str(entry.get("tracks")), _("tracks")
                )
            else:
                name = f"{list(entry.keys())[0]}"
            search_list += f"`{search_track_num}.` {name}\n"

        embed = discord.Embed(
            colour=await ctx.embed_colour(), title=title, description=search_list
        )
        embed.set_footer(
            text=_("Page {page_num}/{total_pages}").format(
                page_num=page_num, total_pages=search_num_pages
            )
        )
        return embed

    async def _search_button_action(
        self, ctx: commands.Context, tracks: List, emoji: str, page: int
    ):
        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, guild=ctx.guild)
        if player.status == PlayerStatus.NOT_READY:
            if self.lavalink_connection_aborted:
                msg = _("Connection to Lavalink has failed.")
                description = EmptyEmbed
                if await self.bot.is_owner(ctx.author):
                    description = _("Please check your console or logs for details.")
                return await self.send_embed_msg(ctx, title=msg, description=description)
            try:
                player.store("connect", datetime.datetime.utcnow())
                await player.connect(ctx.author.voice.channel.id)
            except AttributeError:
                return await self.send_embed_msg(ctx, title=_("Connect to a voice channel first."))
            except wavelink.errors.ZeroConnectedNodes:
                return await self.send_embed_msg(
                    ctx, title=_("Connection to Lavalink has not yet been established.")
                )
        guild_data = await self.config.guild(ctx.guild).all()
        if player.queue.qsize() >= 10000:
            return await self.send_embed_msg(
                ctx, title=_("Unable To Play Tracks"), description=_("Queue size limit reached.")
            )
        if not await self.maybe_charge_requester(ctx, guild_data["jukebox_price"]):
            return
        try:
            if emoji == "\N{DIGIT ONE}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = tracks[0 + (page * 5)]
            elif emoji == "\N{DIGIT TWO}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = tracks[1 + (page * 5)]
            elif emoji == "\N{DIGIT THREE}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = tracks[2 + (page * 5)]
            elif emoji == "\N{DIGIT FOUR}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = tracks[3 + (page * 5)]
            elif emoji == "\N{DIGIT FIVE}\N{COMBINING ENCLOSING KEYCAP}":
                search_choice = tracks[4 + (page * 5)]
            else:
                search_choice = tracks[0 + (page * 5)]
        except IndexError:
            search_choice = tracks[-1]
        if not hasattr(search_choice, "is_local") and getattr(search_choice, "uri", None):
            description = await self.get_track_description(
                search_choice, self.local_folder_current_path
            )
        else:
            search_choice = Query.process_input(search_choice, self.local_folder_current_path)
            if search_choice.is_local:
                if (
                    search_choice.local_track_path.exists()
                    and search_choice.local_track_path.is_dir()
                ):
                    return await ctx.invoke(self.command_search, query=search_choice)
                elif (
                    search_choice.local_track_path.exists()
                    and search_choice.local_track_path.is_file()
                ):
                    search_choice.invoked_from = "localtrack"
            return await ctx.invoke(self.command_play, query=search_choice)

        songembed = discord.Embed(title=_("Track Enqueued"), description=description)
        queue_dur = await self.queue_duration(ctx)
        queue_total_duration = self.format_time(queue_dur)
        before_queue_length = player.queue.qsize()

        if not await self.is_query_allowed(
            self.config,
            ctx.guild,
            (
                f"{search_choice.title} {search_choice.author} {search_choice.uri} "
                f"{str(Query.process_input(search_choice, self.local_folder_current_path))}"
            ),
        ):
            if IS_DEBUG:
                log.debug(f"Query is not allowed in {ctx.guild} ({ctx.guild.id})")
            self.update_player_lock(ctx, False)
            return await self.send_embed_msg(
                ctx, title=_("This track is not allowed in this server.")
            )
        elif guild_data["maxlength"] > 0:

            if self.is_track_too_long(search_choice.length, guild_data["maxlength"]):
                search_choice.extras.update(
                    {
                        "enqueue_time": int(time.time()),
                        "vc": player.channel.id,
                        "requester": ctx.author.id,
                    }
                )
                await player.add(ctx.author, search_choice)
                player.maybe_shuffle()
                self.bot.dispatch(
                    "red_audio_track_enqueue", player.guild, search_choice, ctx.author
                )
            else:
                return await self.send_embed_msg(ctx, title=_("Track exceeds maximum length."))
        else:
            search_choice.extras.update(
                {
                    "enqueue_time": int(time.time()),
                    "vc": player.channel.id,
                    "requester": ctx.author.id,
                }
            )
            await player.add(ctx.author, search_choice)
            player.maybe_shuffle()
            self.bot.dispatch("red_audio_track_enqueue", player.guild, search_choice, ctx.author)

        if not guild_data["shuffle"] and queue_dur > 0:
            songembed.set_footer(
                text=_("{time} until track playback: #{position} in queue").format(
                    time=queue_total_duration, position=before_queue_length + 1
                )
            )

        if not player.current:
            await player.play()
        return await self.send_embed_msg(ctx, embed=songembed)

    async def _format_search_options(self, search_choice):
        query = Query.process_input(search_choice, self.local_folder_current_path)
        description = await self.get_track_description(
            search_choice, self.local_folder_current_path
        )
        return description, query

    async def _build_search_page(
        self, ctx: commands.Context, tracks: List, page_num: int
    ) -> discord.Embed:
        search_num_pages = math.ceil(len(tracks) / 5)
        search_idx_start = (page_num - 1) * 5
        search_idx_end = search_idx_start + 5
        search_list = ""
        command = ctx.invoked_with
        folder = False
        async for i, track in AsyncIter(tracks[search_idx_start:search_idx_end]).enumerate(
            start=search_idx_start
        ):
            search_track_num = i + 1
            if search_track_num > 5:
                search_track_num = search_track_num % 5
            if search_track_num == 0:
                search_track_num = 5
            try:
                query = Query.process_input(track.uri, self.local_folder_current_path)
                if query.is_local:
                    search_list += "`{0}.` **{1}**\n[{2}]\n".format(
                        search_track_num,
                        track.title,
                        LocalPath(track.uri, self.local_folder_current_path).to_string_user(),
                    )
                else:
                    search_list += "`{0}.` **[{1}]({2})**\n".format(
                        search_track_num, track.title, track.uri
                    )
            except AttributeError:
                track = Query.process_input(track, self.local_folder_current_path)
                if track.is_local and command != "search":
                    search_list += "`{}.` **{}**\n".format(
                        search_track_num, track.to_string_user()
                    )
                    if track.is_album:
                        folder = True
                else:
                    search_list += "`{}.` **{}**\n".format(
                        search_track_num, track.to_string_user()
                    )
        if hasattr(tracks[0], "uri") and hasattr(tracks[0], "track_identifier"):
            title = _("Tracks Found:")
            footer = _("search results")
        elif folder:
            title = _("Folders Found:")
            footer = _("local folders")
        else:
            title = _("Files Found:")
            footer = _("local tracks")
        embed = discord.Embed(
            colour=await ctx.embed_colour(), title=title, description=search_list
        )
        embed.set_footer(
            text=(_("Page {page_num}/{total_pages}") + " | {num_results} {footer}").format(
                page_num=page_num,
                total_pages=search_num_pages,
                num_results=len(tracks),
                footer=footer,
            )
        )
        return embed
