# -*- coding: utf-8 -*-
from .reporter import Reporter


def setup(bot):
    bot.add_cog(Reporter(bot))
