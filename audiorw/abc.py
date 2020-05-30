# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
from abc import ABC
from typing import TYPE_CHECKING

# Cog Dependencies
from redbot.core import Config
from redbot.core.bot import Red

if TYPE_CHECKING:
    pass


class MixinMeta(ABC):
    """Base class for well behaved type hint detection with composite class.

    Basically, to keep developers sane when not all attributes are defined in each mixin.
    """

    bot: Red
    config: Config
