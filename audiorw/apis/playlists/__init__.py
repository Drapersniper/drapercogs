# -*- coding: utf-8 -*-
# Standard Library
import concurrent
import json
import logging

from concurrent.futures.thread import ThreadPoolExecutor
from types import SimpleNamespace
from typing import List, MutableMapping, Optional, Union

# Cog Dependencies
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.dbtools import APSWConnectionWrapper

# Cog Relative Imports
from ...classes.dataclasses import PlaylistFetchResult
from ...classes.playlists import PlaylistScope
from ...logging import debug_exc_log
from ...utilities import sql
from .legacy import PlaylistCompat23

__log__ = logging.getLogger("red.cogs.Audio.api.Playlists")
__all__ = {"PlaylistWrapper", "PlaylistCompat23"}


class PlaylistWrapper:
    def __init__(self, bot: Red, config: Config, conn: APSWConnectionWrapper) -> None:
        self.bot = bot
        self.database = conn
        self.config = config
        self.statement = SimpleNamespace()
        self.statement.pragma_temp_store = sql.pragmas.SET_temp_store
        self.statement.pragma_journal_mode = sql.pragmas.SET_journal_mode
        self.statement.pragma_read_uncommitted = sql.pragmas.SET_read_uncommitted
        self.statement.set_user_version = sql.pragmas.SET_user_version
        self.statement.get_user_version = sql.pragmas.FETCH_user_version
        self.statement.create_table = sql.playlists.CREATE_TABLE
        self.statement.create_index = sql.playlists.CREATE_INDEX

        self.statement.upsert = sql.playlists.UPSERT
        self.statement.delete = sql.playlists.DELETE
        self.statement.delete_scope = sql.playlists.DELETE_SCOPE
        self.statement.delete_scheduled = sql.playlists.DELETE_SCHEDULED

        self.statement.get_one = sql.playlists.FETCH
        self.statement.get_all = sql.playlists.FETCH_ALL
        self.statement.get_all_with_filter = sql.playlists.FETCH_ALL_WITH_FILTER
        self.statement.get_all_converter = sql.playlists.FETCH_ALL_CONVERTER

    async def init(self) -> None:
        """Initialize the Playlist table."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.database.cursor().execute, self.statement.pragma_temp_store)
            executor.submit(self.database.cursor().execute, self.statement.pragma_journal_mode)
            executor.submit(self.database.cursor().execute, self.statement.pragma_read_uncommitted)
            executor.submit(self.database.cursor().execute, self.statement.create_table)
            executor.submit(self.database.cursor().execute, self.statement.create_index)

    @staticmethod
    def get_scope_type(scope: str) -> int:
        """Convert a scope to a numerical identifier."""
        if scope == PlaylistScope.GLOBAL.value:
            table = 1
        elif scope == PlaylistScope.USER.value:
            table = 3
        else:
            table = 2
        return table

    async def fetch(self, scope: str, playlist_id: int, scope_id: int) -> PlaylistFetchResult:
        """Fetch a single playlist."""
        scope_type = self.get_scope_type(scope)

        with ThreadPoolExecutor(max_workers=1) as executor:
            for future in concurrent.futures.as_completed(
                [
                    executor.submit(
                        self.database.cursor().execute,
                        self.statement.get_one,
                        (
                            {
                                "playlist_id": playlist_id,
                                "scope_id": scope_id,
                                "scope_type": scope_type,
                            }
                        ),
                    )
                ]
            ):
                try:
                    row_result = future.result()
                except Exception as exc:
                    debug_exc_log(__log__, exc, "Failed to completed playlist fetch from database")
            row = row_result.fetchone()
            if row:
                row = PlaylistFetchResult(*row)
        return row

    async def fetch_all(
        self, scope: str, scope_id: int, author_id: Optional[int] = None
    ) -> List[PlaylistFetchResult]:
        """Fetch all playlists."""
        scope_type = self.get_scope_type(scope)
        output = []
        with ThreadPoolExecutor(max_workers=1) as executor:
            if author_id is not None:
                for future in concurrent.futures.as_completed(
                    [
                        executor.submit(
                            self.database.cursor().execute,
                            self.statement.get_all_with_filter,
                            (
                                {
                                    "scope_type": scope_type,
                                    "scope_id": scope_id,
                                    "author_id": author_id,
                                }
                            ),
                        )
                    ]
                ):
                    try:
                        row_result = future.result()
                    except Exception as exc:
                        debug_exc_log(
                            __log__, exc, "Failed to completed playlist fetch from database"
                        )
                        return []
            else:
                for future in concurrent.futures.as_completed(
                    [
                        executor.submit(
                            self.database.cursor().execute,
                            self.statement.get_all,
                            ({"scope_type": scope_type, "scope_id": scope_id}),
                        )
                    ]
                ):
                    try:
                        row_result = future.result()
                    except Exception as exc:
                        debug_exc_log(
                            __log__, exc, "Failed to completed playlist fetch from database"
                        )
                        return []
        async for row in AsyncIter(row_result):
            output.append(PlaylistFetchResult(*row))
        return output

    async def fetch_all_converter(
        self, scope: str, playlist_name: str, playlist_id: Union[int, str]
    ) -> List[PlaylistFetchResult]:
        """Fetch all playlists with the specified filter."""
        scope_type = self.get_scope_type(scope)
        try:
            playlist_id = int(playlist_id)
        except Exception as exc:
            debug_exc_log(__log__, exc, "Failed converting playlist_id to int")
            playlist_id = -1

        output = []
        with ThreadPoolExecutor(max_workers=1) as executor:
            for future in concurrent.futures.as_completed(
                [
                    executor.submit(
                        self.database.cursor().execute,
                        self.statement.get_all_converter,
                        (
                            {
                                "scope_type": scope_type,
                                "playlist_name": playlist_name,
                                "playlist_id": playlist_id,
                            }
                        ),
                    )
                ]
            ):
                try:
                    row_result = future.result()
                except Exception as exc:
                    debug_exc_log(__log__, exc, "Failed to completed fetch from database")

            async for row in AsyncIter(row_result):
                output.append(PlaylistFetchResult(*row))
        return output

    async def delete(self, scope: str, playlist_id: int, scope_id: int) -> None:
        """Deletes a single playlists."""
        scope_type = self.get_scope_type(scope)
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(
                self.database.cursor().execute,
                self.statement.delete,
                ({"playlist_id": playlist_id, "scope_id": scope_id, "scope_type": scope_type}),
            )

    async def delete_scheduled(self) -> None:
        """Clean up database from all deleted playlists."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.database.cursor().execute, self.statement.delete_scheduled)

    async def drop(self, scope: str) -> None:
        """Delete all playlists in a scope."""
        scope_type = self.get_scope_type(scope)
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(
                self.database.cursor().execute,
                self.statement.delete_scope,
                ({"scope_type": scope_type}),
            )

    async def create_table(self) -> None:
        """Create the playlist table."""
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(self.database.cursor().execute, sql.playlists.CREATE_TABLE)

    async def upsert(
        self,
        scope: str,
        playlist_id: int,
        playlist_name: str,
        scope_id: int,
        author_id: int,
        playlist_url: Optional[str],
        tracks: List[MutableMapping],
    ) -> None:
        """Insert or update a playlist into the database."""
        scope_type = self.get_scope_type(scope)
        with ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(
                self.database.cursor().execute,
                self.statement.upsert,
                {
                    "scope_type": str(scope_type),
                    "playlist_id": int(playlist_id),
                    "playlist_name": str(playlist_name),
                    "scope_id": int(scope_id),
                    "author_id": int(author_id),
                    "playlist_url": playlist_url,
                    "tracks": json.dumps(tracks),
                },
            )
