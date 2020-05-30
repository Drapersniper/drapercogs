# -*- coding: utf-8 -*-
# Standard Library
import logging

# Cog Relative Imports
from ...classes.meta import CompositeMetaClass
from .cog import AudioEvents
from .dpy import DpyEvents
from .lavalink import LavalinkEvents
from .red import RedEvents

__log__ = logging.getLogger("red.cogs.Audio.cog.Events")


class Events(AudioEvents, DpyEvents, LavalinkEvents, RedEvents, metaclass=CompositeMetaClass):
    """Class joining all event subclasses."""
