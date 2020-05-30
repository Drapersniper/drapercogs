# -*- coding: utf-8 -*-
# Standard Library
import itertools
import logging
import time

from typing import List, Union

# Cog Dependencies
import aiohttp
import discord
import wavelink

from discord.embeds import EmptyEmbed
from redbot.core import commands
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import bold, escape

# Cog Relative Imports
from ...audio_dataclasses import _PARTIALLY_SUPPORTED_MUSIC_EXT, Query
from ...audio_logging import IS_DEBUG, debug_exc_log
from ...errors import QueryUnauthorized, SpotifyFetchError, TrackEnqueueError
from ...utils import Notifier
from ...wavelink_overrides import Player, PlayerStatus, Track
from ..abc import MixinMeta
from ..cog_utils import CompositeMetaClass, _

log = logging.getLogger("red.cogs.Audio.cog.Utilities.player")


class PlayerUtilities(MixinMeta, metaclass=CompositeMetaClass):
    async def _get_spotify_tracks(
        self, ctx: commands.Context, query: Query, forced: bool = False
    ) -> Union[discord.Message, List[Track], Track]:
        if ctx.invoked_with in ["play", "genre"]:
            enqueue_tracks = True
        else:
            enqueue_tracks = False
        player: Player = self.bot.wavelink.get_player(
            ctx.guild.id, cls=Player, guild=ctx.guild, channel=ctx.author.voice.channel
        )
        api_data = await self._check_api_tokens()
        if any([not api_data["spotify_client_id"], not api_data["spotify_client_secret"]]):
            return await self.send_embed_msg(
                ctx,
                title=_("Invalid Environment"),
                description=_(
                    "The owner needs to set the Spotify client ID and Spotify client secret, "
                    "before Spotify URLs or codes can be used. "
                    "\nSee `{prefix}audioset spotifyapi` for instructions."
                ).format(prefix=ctx.prefix),
            )
        elif not api_data["youtube_api"]:
            return await self.send_embed_msg(
                ctx,
                title=_("Invalid Environment"),
                description=_(
                    "The owner needs to set the YouTube API key before Spotify URLs or "
                    "codes can be used.\nSee `{prefix}audioset youtubeapi` for instructions."
                ).format(prefix=ctx.prefix),
            )
        try:
            if self.play_lock[ctx.message.guild.id]:
                return await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Get Tracks"),
                    description=_("Wait until the playlist has finished loading."),
                )
        except KeyError:
            pass

        if query.single_track:
            try:
                res = await self.api_interface.spotify_query(
                    ctx, "track", query.id, skip_youtube=True, notifier=None
                )
                if not res:
                    title = _("Nothing found.")
                    embed = discord.Embed(title=title)
                    if query.is_local and query.suffix in _PARTIALLY_SUPPORTED_MUSIC_EXT:
                        title = _("Track is not playable.")
                        description = _(
                            "**{suffix}** is not a fully supported "
                            "format and some tracks may not play."
                        ).format(suffix=query.suffix)
                        embed = discord.Embed(title=title, description=description)
                    return await self.send_embed_msg(ctx, embed=embed)
            except SpotifyFetchError as error:
                self.update_player_lock(ctx, False)
                return await self.send_embed_msg(
                    ctx, title=_(error.message).format(prefix=ctx.prefix)
                )
            self.update_player_lock(ctx, False)
            try:
                if enqueue_tracks:
                    new_query = Query.process_input(res[0], self.local_folder_current_path)
                    new_query.start_time = query.start_time
                    return await self._enqueue_tracks(ctx, new_query)
                else:
                    query = Query.process_input(res[0], self.local_folder_current_path)
                    try:
                        result, called_api = await self.api_interface.fetch_track(
                            ctx, player, query
                        )
                    except TrackEnqueueError:
                        self.update_player_lock(ctx, False)
                        return await self.send_embed_msg(
                            ctx,
                            title=_("Unable to Get Track"),
                            description=_(
                                "I'm unable get a track from Lavalink at the moment, "
                                "try again in a few minutes."
                            ),
                        )
                    tracks = result.tracks
                    if not tracks:
                        embed = discord.Embed(title=_("Nothing found."))
                        if query.is_local and query.suffix in _PARTIALLY_SUPPORTED_MUSIC_EXT:
                            embed = discord.Embed(title=_("Track is not playable."))
                            embed.description = _(
                                "**{suffix}** is not a fully supported format and some "
                                "tracks may not play."
                            ).format(suffix=query.suffix)
                        return await self.send_embed_msg(ctx, embed=embed)
                    single_track = tracks[0]
                    single_track.start_timestamp = query.start_time * 1000
                    single_track = [single_track]

                    return single_track

            except KeyError:
                self.update_player_lock(ctx, False)
                return await self.send_embed_msg(
                    ctx,
                    title=_("Invalid Environment"),
                    description=_(
                        "The Spotify API key or client secret has not been set properly. "
                        "\nUse `{prefix}audioset spotifyapi` for instructions."
                    ).format(prefix=ctx.prefix),
                )
        elif query.is_album or query.is_playlist:
            self.update_player_lock(ctx, True)
            track_list = await self.fetch_spotify_playlist(
                ctx,
                "album" if query.is_album else "playlist",
                query,
                enqueue_tracks,
                forced=forced,
            )
            self.update_player_lock(ctx, False)
            return track_list
        else:
            return await self.send_embed_msg(
                ctx,
                title=_("Unable To Find Tracks"),
                description=_("This doesn't seem to be a supported Spotify URL or code."),
            )

    async def _enqueue_tracks(
        self, ctx: commands.Context, query: Union[Query, list], enqueue: bool = True
    ) -> Union[discord.Message, List[Track], Track]:
        player: Player = self.bot.wavelink.get_player(
            ctx.guild.id, cls=Player, guild=ctx.guild, channel=ctx.author.voice.channel
        )
        try:
            if self.play_lock[ctx.message.guild.id]:
                return await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Get Tracks"),
                    description=_("Wait until the playlist has finished loading."),
                )
        except KeyError:
            self.update_player_lock(ctx, True)
        guild_data = await self.config.guild(ctx.guild).all()
        first_track_only = False
        single_track = None
        index = None
        playlist_data = None
        playlist_url = None
        seek = 0
        if type(query) is not list:
            if not await self.is_query_allowed(
                self.config, ctx.guild, f"{query}", query_obj=query
            ):
                raise QueryUnauthorized(
                    _("{query} is not an allowed query.").format(query=query.to_string_user())
                )
            if query.single_track:
                first_track_only = True
                index = query.track_index
                if query.start_time:
                    seek = query.start_time
            try:
                result, called_api = await self.api_interface.fetch_track(ctx, player, query)
            except TrackEnqueueError:
                self.update_player_lock(ctx, False)
                return await self.send_embed_msg(
                    ctx,
                    title=_("Unable to Get Track"),
                    description=_(
                        "I'm unable get a track from Lavalink at the moment, "
                        "try again in a few minutes."
                    ),
                )
            tracks = result.tracks
            playlist_data = result.playlist_info
            if not enqueue:
                return tracks
            if not tracks:
                self.update_player_lock(ctx, False)
                title = _("Nothing found.")
                embed = discord.Embed(title=title)
                if result.exception_message:
                    embed.set_footer(text=result.exception_message[:2000].replace("\n", ""))
                if await self.config.use_external_lavalink() and query.is_local:
                    embed.description = _(
                        "Local tracks will not work "
                        "if the `Lavalink.jar` cannot see the track.\n"
                        "This may be due to permissions or because Lavalink.jar is being run "
                        "in a different machine than the local tracks."
                    )
                elif query.is_local and query.suffix in _PARTIALLY_SUPPORTED_MUSIC_EXT:
                    title = _("Track is not playable.")
                    embed = discord.Embed(title=title)
                    embed.description = _(
                        "**{suffix}** is not a fully supported format and some "
                        "tracks may not play."
                    ).format(suffix=query.suffix)
                return await self.send_embed_msg(ctx, embed=embed)
        else:
            tracks = query
        queue_dur = await self.queue_duration(ctx)
        queue_total_duration = self.format_time(queue_dur)
        before_queue_length = player.queue.qsize()

        if not first_track_only and len(tracks) > 1:
            # a list of Tracks where all should be enqueued
            # this is a Spotify playlist already made into a list of Tracks or a
            # url where Lavalink handles providing all Track objects to use, like a
            # YouTube or Soundcloud playlist
            if player.queue.qsize() >= 10000:
                return await self.send_embed_msg(ctx, title=_("Queue size limit reached."))
            track_len = 0
            empty_queue = player.queue.empty()
            async for track in AsyncIter(tracks):
                if player.queue.qsize() >= 10000:
                    continue
                if not await self.is_query_allowed(
                    self.config,
                    ctx.guild,
                    (
                        f"{track.title} {track.author} {track.uri} "
                        f"{str(Query.process_input(track, self.local_folder_current_path))}"
                    ),
                ):
                    if IS_DEBUG:
                        log.debug(f"Query is not allowed in {ctx.guild} ({ctx.guild.id})")
                elif guild_data["maxlength"] > 0:
                    if self.is_track_too_long(track, guild_data["maxlength"]):
                        track_len += 1
                        track.extras.update(
                            {
                                "enqueue_time": int(time.time()),
                                "vc": player.channel.id,
                                "requester": ctx.author.id,
                            }
                        )
                        await player.add(ctx.author, track)
                        self.bot.dispatch(
                            "red_audio_track_enqueue", player.guild, track, ctx.author
                        )

                else:
                    track_len += 1
                    track.extras.update(
                        {
                            "enqueue_time": int(time.time()),
                            "vc": player.channel.id,
                            "requester": ctx.author.id,
                        }
                    )
                    await player.add(ctx.author, track)
                    self.bot.dispatch("red_audio_track_enqueue", player.guild, track, ctx.author)
            player.maybe_shuffle(0 if empty_queue else 1)

            if len(tracks) > track_len:
                maxlength_msg = " {bad_tracks} tracks cannot be queued.".format(
                    bad_tracks=(len(tracks) - track_len)
                )
            else:
                maxlength_msg = ""
            playlist_name = escape(
                playlist_data.name if playlist_data else _("No Title"), formatting=True
            )
            embed = discord.Embed(
                description=bold(f"[{playlist_name}]({playlist_url})")
                if playlist_url
                else playlist_name,
                title=_("Playlist Enqueued"),
            )
            embed.set_footer(
                text=_("Added {num} tracks to the queue.{maxlength_msg}").format(
                    num=track_len, maxlength_msg=maxlength_msg
                )
            )
            if not guild_data["shuffle"] and queue_dur > 0:
                embed.set_footer(
                    text=_(
                        "{time} until start of playlist playback: starts at #{position} in queue"
                    ).format(time=queue_total_duration, position=before_queue_length + 1)
                )
            if not player.current:
                await player.play()
            self.update_player_lock(ctx, False)
            message = await self.send_embed_msg(ctx, embed=embed)
            return tracks or message
        else:
            single_track = None
            # a ytsearch: prefixed item where we only need the first Track returned
            # this is in the case of [p]play <query>, a single Spotify url/code
            # or this is a localtrack item
            try:
                if player.queue.qsize() >= 10000:
                    return await self.send_embed_msg(ctx, title=_("Queue size limit reached."))

                single_track = (
                    tracks if isinstance(tracks, Track) else tracks[index] if index else tracks[0]
                )
                if seek and seek > 0:
                    single_track.start_timestamp = seek * 1000
                if not await self.is_query_allowed(
                    self.config,
                    ctx.guild,
                    (
                        f"{single_track.title} {single_track.author} {single_track.uri} "
                        f"{str(Query.process_input(single_track, self.local_folder_current_path))}"
                    ),
                ):
                    if IS_DEBUG:
                        log.debug(f"Query is not allowed in {ctx.guild} ({ctx.guild.id})")
                    self.update_player_lock(ctx, False)
                    return await self.send_embed_msg(
                        ctx, title=_("This track is not allowed in this server.")
                    )
                elif guild_data["maxlength"] > 0:
                    if self.is_track_too_long(single_track, guild_data["maxlength"]):
                        single_track.extras.update(
                            {
                                "enqueue_time": int(time.time()),
                                "vc": player.channel.id,
                                "requester": ctx.author.id,
                            }
                        )
                        await player.add(ctx.author, single_track)
                        player.maybe_shuffle()
                        self.bot.dispatch(
                            "red_audio_track_enqueue", player.guild, single_track, ctx.author,
                        )
                    else:
                        self.update_player_lock(ctx, False)
                        return await self.send_embed_msg(
                            ctx, title=_("Track exceeds maximum length.")
                        )

                else:
                    single_track.extras.update(
                        {
                            "enqueue_time": int(time.time()),
                            "vc": player.channel.id,
                            "requester": ctx.author.id,
                        }
                    )
                    await player.add(ctx.author, single_track)
                    player.maybe_shuffle()
                    self.bot.dispatch(
                        "red_audio_track_enqueue", player.guild, single_track, ctx.author
                    )
            except IndexError:
                self.update_player_lock(ctx, False)
                title = _("Nothing found")
                desc = EmptyEmbed
                if await self.bot.is_owner(ctx.author):
                    desc = _("Please check your console or logs for details.")
                return await self.send_embed_msg(ctx, title=title, description=desc)
            description = await self.get_track_description(
                single_track, self.local_folder_current_path
            )
            embed = discord.Embed(title=_("Track Enqueued"), description=description)
            if not guild_data["shuffle"] and queue_dur > 0:
                embed.set_footer(
                    text=_("{time} until track playback: #{position} in queue").format(
                        time=queue_total_duration, position=before_queue_length + 1
                    )
                )

        if not player.current:
            await player.play()
        self.update_player_lock(ctx, False)
        message = await self.send_embed_msg(ctx, embed=embed)
        return single_track or message

    async def fetch_spotify_playlist(
        self,
        ctx: commands.Context,
        stype: str,
        query: Query,
        enqueue: bool = False,
        forced: bool = False,
    ):
        player: Player = self.bot.wavelink.get_player(
            ctx.guild.id, cls=Player, guild=ctx.guild, channel=ctx.author.voice.channel
        )
        try:
            embed1 = discord.Embed(title=_("Please wait, finding tracks..."))
            playlist_msg = await self.send_embed_msg(ctx, embed=embed1)
            notifier = Notifier(
                ctx,
                playlist_msg,
                {
                    "spotify": _("Getting track {num}/{total}..."),
                    "youtube": _("Matching track {num}/{total}..."),
                    "lavalink": _("Loading track {num}/{total}..."),
                    "lavalink_time": _("Approximate time remaining: {seconds}"),
                },
            )
            track_list = await self.api_interface.spotify_enqueue(
                ctx,
                stype,
                query.id,
                enqueue=enqueue,
                player=player,
                lock=self.update_player_lock,
                notifier=notifier,
                forced=forced,
                query_global=await self.config.cache_level(),
            )
        except SpotifyFetchError as error:
            self.update_player_lock(ctx, False)
            return await self.send_embed_msg(
                ctx,
                title=_("Invalid Environment"),
                description=_(error.message).format(prefix=ctx.prefix),
            )
        except (RuntimeError, aiohttp.ServerDisconnectedError):
            self.update_player_lock(ctx, False)
            error_embed = discord.Embed(
                title=_("The connection was reset while loading the playlist.")
            )
            await self.send_embed_msg(ctx, embed=error_embed)
            return None
        except Exception as e:
            self.update_player_lock(ctx, False)
            raise e
        self.update_player_lock(ctx, False)
        return track_list

    async def maybe_move_player(self, ctx: commands.Context) -> bool:
        try:
            player: Player = self.bot.wavelink.get_player(
                ctx.guild.id, cls=Player, guild=ctx.guild, channel=ctx.author.voice.channel
            )
        except KeyError:
            return False
        try:
            in_channel = sum(
                not m.bot for m in ctx.guild.get_member(self.bot.user.id).voice.channel.members
            )
        except AttributeError:
            return False

        if not ctx.author.voice:
            user_channel = None
        else:
            user_channel = ctx.author.voice.channel

        if in_channel == 0 and user_channel:
            if (
                (player.channel != user_channel)
                and not player.current
                and player.position == 0
                and player.queue.empty()
            ):
                await player.move_to(user_channel)
                return True
        else:
            return False
