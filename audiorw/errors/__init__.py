# -*- coding: utf-8 -*-
from __future__ import annotations

# Cog Dependencies
import aiohttp

from redbot.core import commands
from redbot.core.commands import UserFeedbackCheckFailure

__all__ = {
    "NoChannelProvided",
    "IncorrectChannelError",
    "AudioError",
    "AudioPermissionError",
    "QueryUnauthorized",
    "PlayerError",
    "AudioConnectionError",
    "LavalinkDownloadFailed",
    "TrackEnqueueError",
    "PlayListError",
    "InvalidPlaylistScope",
    "MissingGuild",
    "MissingAuthor",
    "TooManyMatches",
    "NoMatchesFound",
    "NotAllowed",
    "ApiError",
    "SpotifyApiError",
    "SpotifyFetchError",
    "YouTubeApiError",
    "DatabaseError",
    "InvalidTableError",
    "LocalTrackError",
    "InvalidLocalTrack",
    "InvalidLocalTrackFolder",
    "ArgParserFailure",
}


class NoChannelProvided(commands.CommandError):
    """Error raised when no suitable voice channel was supplied."""


class IncorrectChannelError(commands.CommandError):
    """Error raised when commands are issued outside of the players session channel."""


class AudioError(commands.CommandError):
    """Base exception for errors in the Audio cog."""


class AudioPermissionError(AudioError):
    """Base exception for permissions exceptions in the Audio cog."""


class PlayerError(AudioError):
    """Base exception for errors related to the player."""


class AudioConnectionError(AudioError):
    """Base Exception for errors raised due to a downloads/upload issue."""


class QueryUnauthorized(PlayerError, AudioPermissionError):
    """Provided an unauthorized query to audio."""

    def __init__(self, message, *args) -> None:
        self.message = message
        super().__init__(*args)


class LavalinkDownloadFailed(AudioConnectionError, EnvironmentError):
    """Downloading the Lavalink jar failed.

    Attributes
    ----------
    response : aiohttp.ClientResponse
        The response from the server to the failed GET request.
    should_retry : bool
        Whether or not the Audio cog should retry downloading the jar.
    """

    def __init__(
        self, *args, response: aiohttp.ClientResponse, should_retry: bool = False
    ) -> None:
        super().__init__(*args)
        self.response = response
        self.should_retry = should_retry

    def __repr__(self) -> str:
        str_args = [*map(str, self.args), self._response_repr()]
        return f"LavalinkDownloadFailed({', '.join(str_args)}"

    def __str__(self) -> str:
        return f"{super().__str__()} {self._response_repr()}"

    def _response_repr(self) -> str:
        return f"[{self.response.status} {self.response.reason}]"


class TrackEnqueueError(PlayerError):
    """Unable to play track."""


class PlayListError(PlayerError):
    """Base exception for errors related to playlists."""


class InvalidPlaylistScope(PlayListError):
    """Provided playlist scope is not valid."""


class MissingGuild(PlayListError):
    """Trying to access the Guild scope without a guild."""


class MissingAuthor(PlayListError):
    """Trying to access the User scope without an user id."""


class TooManyMatches(PlayListError):
    """Too many playlist match user input."""


class NoMatchesFound(PlayListError):
    """No entries found for this input."""


class NotAllowed(PlayListError):
    """Too many playlist match user input."""


class ApiError(AudioConnectionError):
    """Base exception for API errors in the Audio cog."""


class SpotifyApiError(ApiError):
    """Base exception for Spotify API errors."""


class SpotifyFetchError(SpotifyApiError):
    """Fetching Spotify data failed."""

    def __init__(self, message, *args) -> None:
        self.message = message
        super().__init__(*args)


class YouTubeApiError(ApiError):
    """Base exception for YouTube Data API errors."""


class DatabaseError(AudioError):
    """Base exception for database errors in the Audio cog."""


class InvalidTableError(DatabaseError):
    """Provided table to query is not a valid table."""


class LocalTrackError(AudioError):
    """Base exception for local track errors."""


class InvalidLocalTrack(LocalTrackError):
    """Base exception for local track errors."""


class InvalidLocalTrackFolder(LocalTrackError):
    """Base exception for local track errors."""


class ArgParserFailure(AudioError, UserFeedbackCheckFailure):
    """Raised when parsing an argument fails."""

    def __init__(
        self, cmd: str, user_input: str, custom_help: str = None, ctx_send_help: bool = False
    ) -> None:
        self.cmd = cmd
        self.user_input = user_input
        self.send_cmd_help = ctx_send_help
        self.custom_help_msg = custom_help
        super().__init__()
