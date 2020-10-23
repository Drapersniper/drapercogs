# -*- coding: utf-8 -*-
from contextlib import suppress

from .jsonoverload import DraperDevJson


def setup(bot):
    with suppress(Exception):
        bot.add_cog(DraperDevJson(bot))
