# -*- coding: utf-8 -*-
# Standard Library
import functools

# Cog Relative Imports
from ..converters import lazy_greedy, playlists

__all__ = {"get_lazy_converter", "get_playlist_converter"}


def get_lazy_converter(splitter: str) -> type:
    """Returns a typechecking safe `LazyGreedyConverter` suitable for use with discord.py."""

    class PartialMeta(type(lazy_greedy.LazyGreedyConverter)):
        __call__ = functools.partialmethod(
            type(lazy_greedy.LazyGreedyConverter).__call__, splitter
        )

    class ValidatedConverter(lazy_greedy.LazyGreedyConverter, metaclass=PartialMeta):
        pass

    return ValidatedConverter


def get_playlist_converter() -> type:
    """Returns a typechecking safe `PlaylistConverter` suitable for use with discord.py."""

    class PartialMeta(type(playlists.PlaylistConverter)):
        __call__ = functools.partialmethod(type(playlists.PlaylistConverter).__call__)

    class ValidatedConverter(playlists.PlaylistConverter, metaclass=PartialMeta):
        pass

    return ValidatedConverter
