# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
import logging
import math

# Cog Dependencies
from redbot.core import commands

# Cog Relative Imports
from ...abc import MixinMeta
from ...classes.meta import CompositeMetaClass
from ...utilities.wavelink import Player

__log__ = logging.getLogger("red.cogs.Audio.cog.Utilities.validation")


class ValidationUtilities(MixinMeta, metaclass=CompositeMetaClass):
    def get_votes_required(self, ctx: commands.Context):
        """Method which returns required votes based on amount of members in a channel."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )
        required = math.ceil((len(player.vc.members) - 1) / 2.5)

        if ctx.command.name == "stop" and len(player.vc.members) - 1 == 2:
            required = 2

        return required

    def is_privileged(self, ctx: commands.Context):
        """Check whether the user is an Admin or DJ."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        return player.dj == ctx.author or ctx.author.guild_permissions.kick_members
