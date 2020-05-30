# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
import logging
import typing

# Cog Dependencies
import discord

from redbot.core import commands

# Cog Relative Imports
from ... import errors
from ...abc import MixinMeta
from ...classes.meta import CompositeMetaClass
from ...utilities.wavelink import Player

__log__ = logging.getLogger("red.cogs.Audio.cog.Events.dpy")


class DpyEvents(MixinMeta, metaclass=CompositeMetaClass):
    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ) -> None:
        if member.bot:
            return

        player: Player = self.bot.wavelink.get_player(member.guild.id, cls=Player)

        if not player.channel_id or not player.context:
            player.node.players.pop(member.guild.id)
            return

        channel = self.bot.get_channel(int(player.channel_id))

        if member == player.dj and after.channel is None:
            for m in channel.members:
                if m.bot:
                    continue
                else:
                    player.dj = m
                    return

        elif after.channel == channel and player.dj not in channel.members:
            player.dj = member

    async def cog_command_error(self, ctx: commands.Context, error: Exception) -> typing.NoReturn:
        """Cog wide error handler."""
        if isinstance(error, errors.IncorrectChannelError):
            return

        if isinstance(error, errors.NoChannelProvided):
            return await ctx.send("You must be in a voice channel or provide one to connect to.")

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Cog wide check, which disallows commands in DMs."""
        if not ctx.guild:
            await ctx.send("Music commands are not available in Private Messages.")
            return False

        return True

    async def cog_before_invoke(self, ctx: commands.Context) -> typing.NoReturn:
        """Coroutine called before command invocation.

        We mainly just want to check whether the user is in the players controller channel.
        """
        player: Player = self.bot.wavelink.get_player(ctx.guild.id, cls=Player, context=ctx)

        if player.context and player.context.channel != ctx.channel:
            await ctx.send(
                f"{ctx.author.mention}, you must be in {player.context.channel.mention} for this session."
            )
            raise errors.IncorrectChannelError

        if (
            ctx.command.name == "connect"
            and not player.context
            or self.is_privileged(ctx)
            or not player.channel_id
        ):
            return

        channel = self.bot.get_channel(int(player.channel_id))
        if not channel:
            return

        if player.is_connected and ctx.author not in channel.members:
            await ctx.send(
                f"{ctx.author.mention}, you must be in `{channel.name}` to use voice commands."
            )
            raise errors.IncorrectChannelError
