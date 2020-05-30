# -*- coding: utf-8 -*-
# Standard Library
import logging

# Cog Relative Imports
from ...abc import MixinMeta
from ...classes.meta import CompositeMetaClass

__log__ = logging.getLogger("red.cogs.Audio.cog.Commands.equalizer")


class EqualizerCommands(MixinMeta, metaclass=CompositeMetaClass):
    pass
