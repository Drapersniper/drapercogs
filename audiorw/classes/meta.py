# -*- coding: utf-8 -*-
# Standard Library
from abc import ABC

# Cog Dependencies
from redbot.core import commands


class CompositeMetaClass(type(commands.Cog), type(ABC)):
    """This allows the metaclass used for proper type detection to coexist with discord.py's
    metaclass."""
