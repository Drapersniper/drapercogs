# -*- coding: utf-8 -*-
# Standard Library
from contextlib import suppress

# Cog Relative Imports
from .jsonoverload import DraperDevJson


def setup(bot):
    with suppress(Exception):
        bot.add_cog(DraperDevJson(bot))
