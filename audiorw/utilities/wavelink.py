# -*- coding: utf-8 -*-
# Standard Library
import asyncio
import contextlib
import datetime
import re
import typing

# Cog Dependencies
import async_timeout
import discord
import wavelink

from redbot.core import commands

# Cog Relative Imports
from ..UX import InteractiveController
from ..classes.enums import PlayerStatus
from ..utilities import regex

__all__ = {"Track", "TrackPlaylist", "Player"}


class Track:
    """Wavelink Tack object.

    Attributes
    ------------
    id: str
        The Base64 Track ID.
    info: dict
        The raw track info.
    title: str
        The track title.
    identifier: Optional[str]
        The tracks identifier. could be None depending on track type.
    ytid: Optional[str]
        The tracks YouTube ID. Could be None if ytsearch was not used.
    length:
        The duration of the track.
    duration:
        Alias to length.
    uri: Optional[str]
        The tracks URI. Could be None.
    author: Optional[str]
        The author of the track. Could be None
    is_stream: bool
        Indicated whether the track is a stream or not.
    thumb: Optional[str]
        The thumbnail URL associated with the track. Could be None.
    position: int
        The position of the track.
    seekable: bool
        Whether or not the track is seekable.
    start_timestamp: int
        The track start time.
    extras: dict
        Extra metadata saved in the track object.
    requesting_user: Optional[discord.Member]
        The discord member who requested this track.
    """

    __slots__ = (
        "id",
        "info",
        "query",
        "title",
        "identifier",
        "ytid",
        "length",
        "duration",
        "uri",
        "author",
        "is_stream",
        "dead",
        "thumb",
        "position",
        "seekable",
        "start_timestamp",
        "extras",
        "requesting_user",
    )

    def __init__(
        self,
        identifier: str,
        info: dict,
        query: typing.Optional[str] = None,
        extras: typing.Optional[typing.MutableMapping] = None,
        **kwargs,
    ) -> None:
        self.id = identifier
        self.info = info
        self.query = query

        self.title = info.get("title")
        self.identifier = info.get("identifier")
        self.ytid = self.identifier if re.match(regex.YOUTUBE_ID, self.identifier) else None
        self.length = info.get("length")
        self.duration = self.length
        self.uri = info.get("uri")
        self.author = info.get("author")

        self.is_stream = info.get("isStream")

        self.dead = False

        if self.ytid:
            self.thumb = f"https://img.youtube.com/vi/{self.ytid}/maxresdefault.jpg"
        else:
            self.thumb = None

        self.requesting_user = kwargs.get("requester")
        self.start_timestamp = info.get("timestamp", 0)
        self.seekable = info.get("isSeekable", False)
        self.position = info.get("position")
        self.extras = extras or {}

    @property
    def is_dead(self) -> bool:
        return self.dead

    @property
    def thumbnail(self) -> typing.Optional[str]:
        return self.thumb

    @property
    def requester(self) -> typing.Optional[discord.Member]:
        return self.requesting_user

    @requester.setter
    def requester(self, requester: discord.Member) -> None:
        self.requesting_user = requester

    def __eq__(self, other: typing.Any) -> bool:
        if isinstance(other, Track):
            return self.id == other.id
        return NotImplemented

    def __ne__(self, other: typing.Any) -> bool:
        x = self.__eq__(other)
        if x is not NotImplemented:
            return not x
        return NotImplemented

    def __hash__(self) -> hash:
        return hash((self.id, self.uri))

    def __str__(self) -> str:
        return self.title


class TrackPlaylist:
    """Track Playlist object.

    Attributes
    ------------
    data: dict
        The raw playlist info dict.
    tracks: list
        A list of individual :class:`Track` objects from the playlist.
    """

    def __init__(self, data: dict) -> None:
        self.data = data
        self.tracks = [
            Track(identifier=track["track"], info=track["info"], extras=track.get("extras", {}))
            for track in data["tracks"]
            if track
        ]


wavelink.Track = Track
wavelink.TrackPlaylist = TrackPlaylist


class Votes:
    def __init__(self) -> None:
        self._pause = set()
        self._resume = set()
        self._skip = set()
        self._shuffle = set()
        self._stop = set()

    @property
    def pause(self) -> typing.Set[int]:
        return self._pause

    @property
    def resume(self) -> typing.Set[int]:
        return self._resume

    @property
    def skip(self) -> typing.Set[int]:
        return self._skip

    @property
    def shuffle(self) -> typing.Set[int]:
        return self._shuffle

    @property
    def stop(self) -> typing.Set[int]:
        return self._stop

    def __rep__(self):
        return (
            f"Votes(pause={len(self.pause)}, "
            f"resume={len(self.resume)}, "
            f"skip={len(self.skip)}, "
            f"shuffle={len(self.shuffle)}, "
            f"stop={len(self.stop)})"
        )


class Player(wavelink.Player):
    """Custom wavelink Player class."""

    def __init__(
        self,
        *args,
        vc: typing.Optional[discord.VoiceChannel] = None,
        notify: typing.Optional[discord.TextChannel] = None,
        guild: typing.Optional[discord.Guild] = None,
        context: typing.Optional[commands.Context] = None,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._metadata: typing.MutableMapping[typing.Any, typing.Any] = {}
        self.context: typing.Optional[commands.Context] = context
        if self.context:
            self.dj: discord.Member = self.context.author
            self.guild: discord.Guild = self.context.guild
            self.notification_channel: discord.TextChannel = self.context.channel
            self.vc: typing.Optional[
                discord.VoiceChannel
            ] = self.context.author.voice.channel if self.context.author.voice else None

        self.guild: typing.Optional[discord.Guild] = guild or self.guild
        self.notification_channel: typing.Optional[
            discord.TextChannel
        ] = notify or self.notification_channel
        self.vc: typing.Optional[discord.VoiceChannel] = vc or self.vc

        self.queue: asyncio.Queue = asyncio.Queue()
        self.recent_queue: asyncio.Queue = asyncio.Queue()

        self._shuffle: bool = False
        self._shuffle_bumped: bool = True
        self._repeat: bool = False

        self.controller = None

        self.waiting: bool = False
        self.updating: bool = False

        self.votes: Votes = Votes()

    @property
    def pause_votes(self) -> int:
        return len(self.votes.pause)

    @property
    def resume_votes(self) -> int:
        return len(self.votes.resume)

    @property
    def skip_votes(self) -> int:
        return len(self.votes.skip)

    @property
    def shuffle_votes(self) -> int:
        return len(self.votes.shuffle)

    @property
    def stop_votes(self) -> int:
        return len(self.votes.stop)

    @property
    def status(self):
        if self.is_playing:
            return PlayerStatus.PLAYING
        elif self.is_paused:
            return PlayerStatus.PAUSED
        elif self.is_connected:
            return PlayerStatus.CONNECTED
        else:
            return PlayerStatus.DISCONNECTED

    def store(self, key: typing.Any, value: typing.Any) -> typing.Any:
        """Stores a metadata value by key."""
        self._metadata[key] = value

    def fetch(self, key, default=None):
        """
        Returns a stored metadata value.
        Parameters
        ----------
        key
            Key used to store metadata.
        default
            Optional, used if the key doesn't exist.
        """
        return self._metadata.get(key, default)

    def __repr__(self) -> str:

        return (
            "Red.Player("
            f"status={self.status}, "
            f"queue={self.queue.qsize()}, "
            f"recent_queue={self.recent_queue.qsize()}, "
            f"guild={self.guild.id if self.guild else None}, "
            f"channel={self.vc.id if self.vc else None}, "
            f"notification_channel={self.notification_channel.id if self.notification_channel else None}, "
            f"current='{self.current}', "
            f"volume={self.volume}, "
            f"votes={repr(self.votes)}"
            ")"
        )

    async def play_next(self) -> None:
        if self.waiting:
            return

        # Clear the votes for a new song...
        self.votes.pause.clear()
        self.votes.resume.clear()
        self.votes.skip.clear()
        self.votes.shuffle.clear()
        self.votes.stop.clear()

        self.waiting = True
        track = await self.queue.get()

        await self.play(track)
        self.waiting = False

        # Invoke our players controller...
        await self.invoke_controller()

    async def invoke_controller(self) -> None:
        """Method which updates or sends a new player controller."""
        if self.updating:
            return

        self.updating = True

        if not self.controller:
            self.controller = InteractiveController(embed=self.build_embed(), player=self)
            await self.controller.start(self.context)

        elif not await self.is_position_fresh():
            try:
                await self.controller.message.delete()
            except discord.HTTPException:
                pass

            self.controller.stop()

            self.controller = InteractiveController(embed=self.build_embed(), player=self)
            await self.controller.start(self.context)

        else:
            embed = self.build_embed()
            await self.controller.message.edit(content=None, embed=embed)

        self.updating = False

    def build_embed(self) -> typing.Optional[discord.Embed]:
        """Method which builds our players controller embed."""
        track = self.current
        if not track:
            return

        channel = self.bot.get_channel(int(self.channel_id))
        qsize = self.queue.qsize()

        embed = discord.Embed(title=f"Music Controller | {channel.name}", colour=0xEBB145)
        embed.description = f"Now Playing:\n**`{track.title}`**\n\n"
        embed.set_thumbnail(url=track.thumb)

        embed.add_field(
            name="Duration", value=str(datetime.timedelta(milliseconds=int(track.length)))
        )
        embed.add_field(name="Queue Length", value=str(qsize))
        embed.add_field(name="Volume", value=f"**`{self.volume}%`**")
        embed.add_field(name="Requested By", value=track.requester.mention)
        embed.add_field(name="DJ", value=self.dj.mention)
        embed.add_field(name="Video URL", value=f"[Click Here!]({track.uri})")

        return embed

    async def is_position_fresh(self) -> bool:
        """Method which checks whether the player controller should be remade or updated."""
        try:
            async for message in self.context.channel.history(limit=5):
                if message.id == self.controller.message.id:
                    return True
        except (discord.HTTPException, AttributeError):
            return False

        return False

    async def teardown(self):
        """Clear internal states, remove player controller and disconnect."""
        with contextlib.suppress(discord.HTTPException):
            await self.controller.message.delete()

        self.controller.stop()

        with contextlib.suppress(KeyError):
            await self.destroy()
