import asyncio
import contextlib
import datetime
import logging
import time
from typing import Optional

import discord
import lavalink

from redbot.core import commands

from ...apis.playlist_interface import Playlist, delete_playlist, get_playlist
from ...audio_dataclasses import Query
from ...audio_logging import debug_exc_log
from ...utils import PlaylistScope
from ..abc import MixinMeta
from ..cog_utils import CompositeMetaClass

log = logging.getLogger("red.cogs.Audio.cog.Events.audio")


class AudioEvents(MixinMeta, metaclass=CompositeMetaClass):
    @commands.Cog.listener()
    async def on_red_audio_track_start(
        self, guild: discord.Guild, track: lavalink.Track, requester: discord.Member
    ):
        if not (track and guild):
            return
        self.bot.counter["tracks_played"] += 1
        query = Query.process_input(track, self.local_folder_current_path)
        if track.is_stream:
            self.bot.counter["streams_played"] += 1
            if query.is_youtube:
                self.bot.counter["yt_streams_played"] += 1
            elif query.is_mixer:
                self.bot.counter["mixer_streams_played"] += 1
            elif query.is_twitch:
                self.bot.counter["ttv_streams_played"] += 1
            elif query.is_other:
                self.bot.counter["other_streams_played"] += 1

        if query.is_youtube:
            self.bot.counter["youtube_tracks"] += 1
        elif query.is_soundcloud:
            self.bot.counter["soundcloud_tracks"] += 1
        elif query.is_bandcamp:
            self.bot.counter["bandcamp_tracks"] += 1
        elif query.is_vimeo:
            self.bot.counter["vimeo_tracks"] += 1
        elif query.is_mixer:
            self.bot.counter["mixer_tracks"] += 1
        elif query.is_twitch:
            self.bot.counter["twitch_tracks"] += 1
        elif query.is_other:
            self.bot.counter["other_tracks"] += 1
        track_identifier = track.track_identifier
        if self.playlist_api is not None:
            daily_cache = self._daily_playlist_cache.setdefault(
                guild.id, await self.config.guild(guild).daily_playlists()
            )
            global_daily_playlists = self._daily_global_playlist_cache.setdefault(
                self.bot.user.id, await self.config.daily_playlists()
            )
            today = datetime.date.today()
            midnight = datetime.datetime.combine(today, datetime.datetime.min.time())
            today_id = int(time.mktime(today.timetuple()))
            track = self.track_to_json(track)
            if daily_cache:
                name = f"Daily playlist - {today}"
                playlist: Optional[Playlist]
                try:
                    playlist = await get_playlist(
                        playlist_api=self.playlist_api,
                        playlist_number=today_id,
                        scope=PlaylistScope.GUILD.value,
                        bot=self.bot,
                        guild=guild,
                        author=self.bot.user,
                    )
                except RuntimeError:
                    playlist = None

                if playlist:
                    tracks = playlist.tracks
                    tracks.append(track)
                    await playlist.edit({"tracks": tracks})
                else:
                    playlist = Playlist(
                        bot=self.bot,
                        scope=PlaylistScope.GUILD.value,
                        author=self.bot.user.id,
                        playlist_id=today_id,
                        name=name,
                        playlist_url=None,
                        tracks=[track],
                        guild=guild,
                        playlist_api=self.playlist_api,
                    )
                    await playlist.save()
            if global_daily_playlists:
                global_name = f"Global Daily playlist - {today}"
                try:
                    playlist = await get_playlist(
                        playlist_number=today_id,
                        scope=PlaylistScope.GLOBAL.value,
                        bot=self.bot,
                        guild=guild,
                        author=self.bot.user,
                        playlist_api=self.playlist_api,
                    )
                except RuntimeError:
                    playlist = None
                if playlist:
                    tracks = playlist.tracks
                    tracks.append(track)
                    await playlist.edit({"tracks": tracks})
                else:
                    playlist = Playlist(
                        bot=self.bot,
                        scope=PlaylistScope.GLOBAL.value,
                        author=self.bot.user.id,
                        playlist_id=today_id,
                        name=global_name,
                        playlist_url=None,
                        tracks=[track],
                        guild=guild,
                        playlist_api=self.playlist_api,
                    )
                    await playlist.save()
            too_old = midnight - datetime.timedelta(days=8)
            too_old_id = int(time.mktime(too_old.timetuple()))
            try:
                await delete_playlist(
                    scope=PlaylistScope.GUILD.value,
                    playlist_id=too_old_id,
                    guild=guild,
                    author=self.bot.user,
                    playlist_api=self.playlist_api,
                    bot=self.bot,
                )
            except Exception as err:
                debug_exc_log(log, err, f"Failed to delete daily playlist ID: {too_old_id}")
            try:
                await delete_playlist(
                    scope=PlaylistScope.GLOBAL.value,
                    playlist_id=too_old_id,
                    guild=guild,
                    author=self.bot.user,
                    playlist_api=self.playlist_api,
                    bot=self.bot,
                )
            except Exception as err:
                debug_exc_log(log, err, f"Failed to delete global daily playlist ID: {too_old_id}")
        persist_cache = self._persist_queue_cache.setdefault(
            guild.id, await self.config.guild(guild).persist_queue()
        )
        if persist_cache:
            await self.api_interface.persistent_queue_api.played(
                guild_id=guild.id, track_id=track_identifier
            )

    @commands.Cog.listener()
    async def on_red_audio_queue_end(
        self, guild: discord.Guild, track: lavalink.Track, requester: discord.Member
    ):
        if not (track and guild):
            return
        if self.api_interface is not None and self.playlist_api is not None:
            await self.api_interface.local_cache_api.youtube.clean_up_old_entries()
            await asyncio.sleep(5)
            await self.playlist_api.delete_scheduled()
        await self.api_interface.persistent_queue_api.drop(guild.id)
        await asyncio.sleep(5)
        await self.api_interface.persistent_queue_api.delete_scheduled()

    @commands.Cog.listener()
    async def on_red_audio_track_enqueue(self, guild: discord.Guild, track, requester):
        if not (track and guild):
            return
        self.bot.counter["tracks_enqueued"] += 1
        persist_cache = self._persist_queue_cache.setdefault(
            guild.id, await self.config.guild(guild).persist_queue()
        )
        if persist_cache:
            await self.api_interface.persistent_queue_api.enqueued(
                guild_id=guild.id, room_id=track.extras["vc"], track=track
            )

    @commands.Cog.listener()
    async def on_red_audio_track_end(self, guild, song, requester):
        if not (guild and song):
            return
        mess, ctx, player = self.now_message_cache.get(guild.id, (None, None, None))
        if not mess:
            return
        with contextlib.suppress(discord.HTTPException):
            new_embed = await self.make_now_embed(player, ctx)
            await mess.edit(embed=new_embed)
