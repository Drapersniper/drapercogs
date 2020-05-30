# -*- coding: utf-8 -*-
# Standard Library
import datetime
import json

from dataclasses import dataclass, field
from typing import List, MutableMapping, Optional

# Cog Relative Imports
from ..utilities.wavelink import Track

__all__ = {
    "YouTubeCacheFetchResult",
    "SpotifyCacheFetchResult",
    "LavalinkCacheFetchResult",
    "LavalinkCacheFetchForGlobalResult",
    "PlaylistFetchResult",
    "QueueFetchResult",
}


@dataclass
class YouTubeCacheFetchResult:
    query: Optional[str]
    last_updated: int

    def __post_init__(self) -> None:
        if isinstance(self.last_updated, int):
            self.updated_on: datetime.datetime = datetime.datetime.fromtimestamp(self.last_updated)


@dataclass
class SpotifyCacheFetchResult:
    query: Optional[str]
    last_updated: int

    def __post_init__(self) -> None:
        if isinstance(self.last_updated, int):
            self.updated_on: datetime.datetime = datetime.datetime.fromtimestamp(self.last_updated)


@dataclass
class LavalinkCacheFetchResult:
    query: Optional[MutableMapping]
    last_updated: int

    def __post_init__(self) -> None:
        if isinstance(self.last_updated, int):
            self.updated_on: datetime.datetime = datetime.datetime.fromtimestamp(self.last_updated)

        if isinstance(self.query, str):
            self.query = json.loads(self.query)


@dataclass
class LavalinkCacheFetchForGlobalResult:
    query: str
    data: MutableMapping

    def __post_init__(self) -> None:
        if isinstance(self.data, str):
            self.data_string = str(self.data)
            self.data = json.loads(self.data)


@dataclass
class PlaylistFetchResult:
    playlist_id: int
    playlist_name: str
    scope_id: int
    author_id: int
    playlist_url: Optional[str] = None
    tracks: List[MutableMapping] = field(default_factory=lambda: [])

    def __post_init__(self) -> None:
        if isinstance(self.tracks, str):
            self.tracks = json.loads(self.tracks)


@dataclass
class QueueFetchResult:
    guild_id: int
    room_id: int
    track: dict = field(default_factory=lambda: {})
    track_object: Track = None

    def __post_init__(self) -> None:
        if isinstance(self.track, str):
            self.track = json.loads(self.track)
        if self.track:
            self.track_object = Track(
                identifier=self.track["track"],
                info=self.track["info"],
                extras=self.track.get("extras", {}),
            )
