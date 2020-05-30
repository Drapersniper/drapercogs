# -*- coding: utf-8 -*-
# Standard Library
import logging

# Cog Relative Imports
from ...classes.meta import CompositeMetaClass
from .lavalink import LavalinkTasks
from .player import PlayerTasks
from .startup import StartUpTasks

__log__ = logging.getLogger("red.cogs.Audio.cog.Tasks")


class Tasks(LavalinkTasks, PlayerTasks, StartUpTasks, metaclass=CompositeMetaClass):
    """Class joining all task subclasses."""
