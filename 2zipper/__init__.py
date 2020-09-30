# -*- coding: utf-8 -*-
# Cog Relative Imports
from .zipper import Zipper


def setup(bot):
    bot.add_cog(Zipper(bot))
