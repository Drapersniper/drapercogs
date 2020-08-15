# -*- coding: utf-8 -*-
# Cog Relative Imports
from .memmonitor import MemMonitor


def setup(bot):
    bot.add_cog(MemMonitor(bot))
