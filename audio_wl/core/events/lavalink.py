# -*- coding: utf-8 -*-
# Standard Library
import asyncio
import collections
import contextlib
import logging

# Cog Dependencies
import discord
import wavelink

# Cog Relative Imports
from ...errors import DatabaseError
from ...wavelink_overrides import Player, Track
from ..abc import MixinMeta
from ..cog_utils import CompositeMetaClass, _

log = logging.getLogger("red.cogs.Audio.cog.Events.lavalink")


class LavalinkEvents(MixinMeta, metaclass=CompositeMetaClass):
    async def lavalink_event_handler(self, event: wavelink.WavelinkEvent) -> None:
        player: Player = event.player
        prev_song: Track = player.fetch("prev_song")
        current_track = player.current
        guild = player.guild
        if guild is None:
            return
        guild_id = self.rgetattr(guild, "id", None)
        current_requester = self.rgetattr(current_track, "requester", None)
        current_stream = self.rgetattr(current_track, "is_stream", None)
        current_length = self.rgetattr(current_track, "length", None)
        current_thumbnail = self.rgetattr(current_track, "thumbnail", None)
        current_extras = self.rgetattr(current_track, "extras", {})
        guild_data = await self.config.guild(guild).all()
        repeat = guild_data["repeat"]
        notify = guild_data["notify"]
        disconnect = guild_data["disconnect"]
        autoplay = guild_data["auto_play"]
        description = await self.get_track_description(
            current_track, self.local_folder_current_path
        )
        status = await self.config.status()
        log.debug(f"Received a new lavalink event for {guild_id}: {event}")
        if player.notification_channel is None:
            player.notification_channel = self.bot.get_channel(player.fetch("channel"))
        await self.maybe_reset_error_counter(player)
        if isinstance(event, wavelink.TrackStart):
            self.skip_votes[guild] = []
            playing_song = player.fetch("playing_song")
            requester = player.fetch("requester")
            player.store("prev_song", playing_song)
            player.store("prev_requester", requester)
            player.store("playing_song", current_track)
            player.store("requester", current_requester)
            self.bot.dispatch("red_audio_track_start", guild, current_track, current_requester)
            if guild_id and current_track:
                await self.api_interface.persistent_queue_api.played(
                    guild_id=guild_id, track_id=current_track.id
                )
        if isinstance(event, wavelink.TrackEnd):
            prev_requester = player.fetch("prev_requester")
            self.bot.dispatch("red_audio_track_end", guild, prev_song, prev_requester)
            await player.play()

        if isinstance(event, wavelink.TrackEnd) and player.queue.empty():
            prev_requester = player.fetch("prev_requester")
            self.bot.dispatch("red_audio_queue_end", guild, prev_song, prev_requester)
            if guild_id:
                await self.api_interface.persistent_queue_api.drop(guild_id)
            if (
                autoplay
                and player.queue.empty()
                and player.fetch("playing_song") is not None
                and self.playlist_api is not None
                and self.api_interface is not None
            ):
                try:
                    await self.api_interface.autoplay(player, self.playlist_api)
                except DatabaseError:
                    notify_channel = player.notification_channel
                    if notify_channel:
                        await self.send_embed_msg(
                            notify_channel, title=_("Couldn't get a valid track.")
                        )
                    return
        if isinstance(event, wavelink.TrackStart) and notify:
            notify_channel = player.notification_channel
            if notify_channel:
                if player.fetch("notify_message") is not None:
                    with contextlib.suppress(discord.HTTPException):
                        await player.fetch("notify_message").delete()
                print("events", current_extras.get("autoplay"))
                if (
                    autoplay
                    and current_extras.get("autoplay")
                    and (
                        prev_song is None
                        or (hasattr(prev_song, "extras") and not prev_song.extras.get("autoplay"))
                    )
                ):
                    await self.send_embed_msg(notify_channel, title=_("Auto Play started."))

                if not description:
                    return
                if current_stream:
                    dur = "LIVE"
                else:
                    dur = self.format_time(current_length)

                thumb = None
                if await self.config.guild(guild).thumbnail() and current_thumbnail:
                    thumb = current_thumbnail

                notify_message = await self.send_embed_msg(
                    notify_channel,
                    title=_("Now Playing"),
                    description=description,
                    footer=_("Track length: {length} | Requested by: {user}").format(
                        length=dur, user=current_requester
                    ),
                    thumbnail=thumb,
                )
                player.store("notify_message", notify_message)
        if isinstance(event, wavelink.TrackStart) and status:
            player_check = await self.get_active_player_count()
            await self.update_bot_presence(*player_check)

        if isinstance(event, wavelink.TrackEnd) and status:
            await asyncio.sleep(1)
            if not player.is_playing:
                player_check = await self.get_active_player_count()
                await self.update_bot_presence(*player_check)

        if isinstance(event, wavelink.TrackEnd) and player.queue.empty():
            if not autoplay:
                notify_channel = player.notification_channel
                if notify_channel and notify:
                    await self.send_embed_msg(notify_channel, title=_("Queue ended."))
                if disconnect:
                    self.bot.dispatch("red_audio_audio_disconnect", guild)
                    await player.disconnect()
            if status:
                player_check = await self.get_active_player_count()
                await self.update_bot_presence(*player_check)

        if isinstance(event, (wavelink.TrackStuck, wavelink.TrackException)):
            message_channel = player.notification_channel
            while current_track in player.queue._queue:
                player.queue._queue.remove(current_track)
            if repeat:
                player.current = None
            if not guild_id:
                return
            self._error_counter.setdefault(guild_id, 0)
            if guild_id not in self._error_counter:
                self._error_counter[guild_id] = 0
            early_exit = await self.increase_error_counter(player)
            if early_exit:
                self._disconnected_players[guild_id] = True
                self.play_lock[guild_id] = False
                eq = player.fetch("eq")
                player.queue._queue = collections.deque()
                player.store("playing_song", None)
                if eq:
                    await self.config.custom("EQUALIZER", guild_id).eq_bands.set(eq.bands)
                await player.destroy()
                self.bot.dispatch("red_audio_audio_disconnect", guild)
            if message_channel:
                if early_exit:
                    embed = discord.Embed(
                        colour=await self.bot.get_embed_color(message_channel),
                        title=_("Multiple Errors Detected"),
                        description=_(
                            "Closing the audio player "
                            "due to multiple errors being detected. "
                            "If this persists, please inform the bot owner "
                            "as the Audio cog may be temporally unavailable."
                        ),
                    )
                    await message_channel.send(embed=embed)
                    return
                else:
                    description = description or ""
                    if isinstance(event, wavelink.TrackStuck):
                        embed = discord.Embed(
                            colour=await self.bot.get_embed_color(message_channel),
                            title=_("Track Stuck"),
                            description="{}".format(description),
                        )
                    else:
                        embed = discord.Embed(
                            title=_("Track Error"),
                            colour=await self.bot.get_embed_color(message_channel),
                            description="{}\n{}".format(
                                event.error.replace("\n", ""), description
                            ),
                        )
                    await message_channel.send(embed=embed)
            await player.skip()
