# -*- coding: utf-8 -*-
# Standard Library
from typing import Final

__all__ = {
    "PERSIST_QUEUE_DROP_TABLE",
    "PERSIST_QUEUE_CREATE_TABLE",
    "PERSIST_QUEUE_CREATE_INDEX",
    "PERSIST_QUEUE_PLAYED",
    "PERSIST_QUEUE_DELETE_SCHEDULED",
    "PERSIST_QUEUE_FETCH_ALL",
    "PERSIST_QUEUE_UPSERT",
    "PERSIST_QUEUE_BULK_PLAYED",
}

PERSIST_QUEUE_DROP_TABLE: Final[
    str
] = """
DROP
    TABLE
        IF EXISTS
            persist_queue
;
"""
PERSIST_QUEUE_CREATE_TABLE: Final[
    str
] = """
CREATE
    TABLE
        IF NOT EXISTS
            persist_queue(
                guild_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                track JSON NOT NULL,
                played BOOLEAN DEFAULT FALSE,
                track_id TEXT NOT NULL,
                time INTEGER NOT NULL,
                PRIMARY KEY
                    (
                        guild_id, room_id, track_id
                    )
                )
;
"""
PERSIST_QUEUE_CREATE_INDEX: Final[
    str
] = """
CREATE
    INDEX
        IF NOT EXISTS
            track_index
ON
    persist_queue (
        guild_id, track_id
        )
;
"""
PERSIST_QUEUE_PLAYED: Final[
    str
] = """
UPDATE
    persist_queue
        SET
            played = TRUE
WHERE
    (
        guild_id = :guild_id
        AND
            track_id = :track_id
    )
;
"""
PERSIST_QUEUE_BULK_PLAYED: Final[
    str
] = """
UPDATE
    persist_queue
        SET
            played = TRUE
WHERE
    guild_id = :guild_id
;
"""
PERSIST_QUEUE_DELETE_SCHEDULED: Final[
    str
] = """
DELETE
FROM
    persist_queue
WHERE
    played = TRUE
;
"""
PERSIST_QUEUE_FETCH_ALL: Final[
    str
] = """
SELECT
    guild_id, room_id, track
FROM
    persist_queue
WHERE
    played = FALSE
ORDER BY
    time
;
"""
PERSIST_QUEUE_UPSERT: Final[
    str
] = """ -- noinspection SqlResolve
INSERT INTO
    persist_queue (
        guild_id, room_id, track, played, track_id, time
        )
VALUES
    (
        :guild_id, :room_id, :track, :played, :track_id, :time
    )
ON
    CONFLICT (
        guild_id, room_id, track_id
        )
    DO
        UPDATE
            SET
                time = excluded.time
;
"""
