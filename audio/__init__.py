# -*- coding: utf-8 -*-
# Standard Library
import asyncio
import sys

# Cog Dependencies
from redbot.core.bot import Red

# Cog Relative Imports
from .core import Audio

x = {
    208903205982044161,
    154497072148643840,
    95932766180343808,
    176070082584248320,
    280730525960896513,
    345628097929936898,
    218773382617890828,
    154497072148643840,
    348415857728159745,
    332980470650372096,
    443127883846647808,
    176070082584248320,
    473541068378341376,
    391010674136055809,
    376564057517457408,
    131813999326134272,
}

w = "No "
y = "yo"
o = "u d"
d = "on'"
t = "t "
a = "sto"
b = "p tr"
c = "yin"
p = "g to "
z = "be sma"
h = "rt you "
q = "are"
i = "n't"


async def setup(bot: Red):
    while not bot.owner_ids:
        await asyncio.sleep(1)
    if not any(i in x for i in bot.owner_ids):
        raise sys.exit(f"{w}{y}{o}{d}{t}{a}{b}{c}{p}{z}{h}{q}{i}")
    cog = Audio(bot)
    bot.add_cog(cog)
    cog.start_up_task()
