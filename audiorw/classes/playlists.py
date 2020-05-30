# -*- coding: utf-8 -*-
# Standard Library
import enum

# noinspection PyTypeChecker
from typing import List

__all__ = {"PlaylistScope"}


@enum.unique
class PlaylistScope(enum.Enum):
    GLOBAL = "GLOBALPLAYLIST"
    GUILD = "GUILDPLAYLIST"
    USER = "USERPLAYLIST"

    def __str__(self) -> str:
        return "{0}".format(self.value)

    @staticmethod
    def list() -> List[str]:
        # type: ignore
        return list(map(lambda c: c.value, PlaylistScope))
