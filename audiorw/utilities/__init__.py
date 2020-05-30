# -*- coding: utf-8 -*-
# Standard Library
from pathlib import Path
from typing import Callable, Final

# Cog Dependencies
from redbot import VersionInfo
from redbot.core.i18n import Translator

# Cog Relative Imports
from . import constants, regex, sql
from .converters import get_lazy_converter, get_playlist_converter

__all__ = {
    "__author__",
    "__version__",
    "_",
    "SCHEMA_VERSION",
    "LazyGreedyConverter",
    "PlaylistConverter",
    "constants",
    "regex",
    "sql",
}
__author__ = ["aikaterna", "Draper"]
__version__ = VersionInfo.from_json(
    {"major": 3, "minor": 0, "micro": 0, "dev_release": 1, "releaselevel": "final"}
)

_ = Translator("Audio", Path(__file__).parent)

SCHEMA_VERSION = constants.SCHEMA_VERSION


LazyGreedyConverter: Final[Callable] = get_lazy_converter("--")
PlaylistConverter: Final[Callable] = get_playlist_converter()
