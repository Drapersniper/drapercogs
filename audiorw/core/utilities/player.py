# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
import logging

# Cog Relative Imports
from ...abc import MixinMeta
from ...classes.meta import CompositeMetaClass

__log__ = logging.getLogger("red.cogs.Audio.cog.Utilities.player")


class PlayerUtilities(MixinMeta, metaclass=CompositeMetaClass):
    pass
