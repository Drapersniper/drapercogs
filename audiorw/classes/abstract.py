# -*- coding: utf-8 -*-
__all__ = {"CacheLevel"}


class CacheLevel:
    __slots__ = ("value",)

    def __init__(self, level=0):
        if not isinstance(level, int):
            raise TypeError(
                f"Expected int parameter, received {level.__class__.__name__} instead."
            )
        elif level < 0:
            level = 0
        elif level > 0b11111:
            level = 0b11111

        self.value = level

    def __eq__(self, other):
        return isinstance(other, CacheLevel) and self.value == other.value

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.value)

    def __add__(self, other):
        return CacheLevel(self.value + other.value)

    def __radd__(self, other):
        return CacheLevel(other.value + self.value)

    def __sub__(self, other):
        return CacheLevel(self.value - other.value)

    def __rsub__(self, other):
        return CacheLevel(other.value - self.value)

    def __str__(self):
        return "{0:b}".format(self.value)

    def __format__(self, format_spec):
        return "{r:{f}}".format(r=self.value, f=format_spec)

    def __repr__(self):
        return f"<CacheLevel value={self.value}>"

    def is_subset(self, other):
        """Returns ``True`` if self has the same or fewer caching levels as other."""
        return (self.value & other.value) == self.value

    def is_superset(self, other):
        """Returns ``True`` if self has the same or more caching levels as other."""
        return (self.value | other.value) == self.value

    def is_strict_subset(self, other):
        """Returns ``True`` if the caching level on other are a strict subset of those on self."""
        return self.is_subset(other) and self != other

    def is_strict_superset(self, other):
        """Returns ``True`` if the caching level on other are a strict superset of those on
        self."""
        return self.is_superset(other) and self != other

    __le__ = is_subset
    __ge__ = is_superset
    __lt__ = is_strict_subset
    __gt__ = is_strict_superset

    @classmethod
    def all(cls):
        """A factory method that creates a :class:`CacheLevel` with max caching level."""
        return cls(0b11111)

    @classmethod
    def none(cls):
        """A factory method that creates a :class:`CacheLevel` with no caching."""
        return cls(0)

    @classmethod
    def set_spotify(cls):
        """A factory method that creates a :class:`CacheLevel` with Spotify caching level."""
        return cls(0b00011)

    @classmethod
    def set_youtube(cls):
        """A factory method that creates a :class:`CacheLevel` with YouTube caching level."""
        return cls(0b00100)

    @classmethod
    def set_lavalink(cls):
        """A factory method that creates a :class:`CacheLevel` with lavalink caching level."""
        return cls(0b11000)

    def _bit(self, index: int):
        return bool((self.value >> index) & 1)

    def _set(self, index: int, value: bool):
        if value is True:
            self.value |= 1 << index
        elif value is False:
            self.value &= ~(1 << index)
        else:
            raise TypeError("Value to set for CacheLevel must be a bool.")

    @property
    def lavalink(self):
        """:class:`bool`: Returns ``True`` if a user can deafen other users."""
        return self._bit(4)

    @lavalink.setter
    def lavalink(self, value: bool):
        self._set(4, value)

    @property
    def youtube(self):
        """:class:`bool`: Returns ``True`` if a user can move users between other voice
        channels."""
        return self._bit(2)

    @youtube.setter
    def youtube(self, value: bool):
        self._set(2, value)

    @property
    def spotify(self):
        """:class:`bool`: Returns ``True`` if a user can use voice activation in voice channels."""
        return self._bit(1)

    @spotify.setter
    def spotify(self, value: bool):
        self._set(1, value)
