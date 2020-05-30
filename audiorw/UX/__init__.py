# -*- coding: utf-8 -*-
from __future__ import annotations

# Standard Library
import copy

from typing import TYPE_CHECKING

# Cog Dependencies
import discord

from discord.ext import menus
from redbot.core import commands

if TYPE_CHECKING:
    from ..utilities.wavelink import Player


class InteractiveController(menus.Menu):
    """The Players interactive controller menu class."""

    def __init__(self, *, embed: discord.Embed, player: Player) -> None:
        super().__init__(timeout=None)

        self.embed = embed
        self.player = player

    def update_context(self, payload: discord.RawReactionActionEvent) -> commands.Context:
        """Update our context with the user who reacted."""
        ctx = copy.copy(self.ctx)
        ctx.author = payload.member

        return ctx

    def reaction_check(self, payload: discord.RawReactionActionEvent) -> bool:
        if payload.event_type == "REACTION_REMOVE":
            return False

        if not payload.member:
            return False
        if payload.member.bot:
            return False
        if payload.message_id != self.message.id:
            return False
        if payload.member not in self.bot.get_channel(int(self.player.channel_id)).members:
            return False

        return payload.emoji in self.buttons

    async def send_initial_message(
        self, ctx: commands.Context, channel: discord.TextChannel
    ) -> discord.Message:
        return await channel.send(embed=self.embed)

    @menus.button(emoji="\u25B6")
    async def resume_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Resume button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("resume")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23F8")
    async def pause_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Pause button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("pause")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23F9")
    async def stop_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Stop button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("stop")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u23ED")
    async def skip_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Skip button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("skip")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F500")
    async def shuffle_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Shuffle button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("shuffle")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u2795")
    async def volup_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Volume up button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("vol_up")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\u2796")
    async def voldown_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Volume down button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("vol_down")
        ctx.command = command

        await self.bot.invoke(ctx)

    @menus.button(emoji="\U0001F1F6")
    async def queue_command(self, payload: discord.RawReactionActionEvent) -> None:
        """Player queue button."""
        ctx = self.update_context(payload)

        command = self.bot.get_command("queue")
        ctx.command = command

        await self.bot.invoke(ctx)


class PaginatorSource(menus.ListPageSource):
    """Player queue paginator class."""

    def __init__(self, entries, *, per_page=8) -> None:
        super().__init__(entries, per_page=per_page)

    async def format_page(self, menu: menus.Menu, page) -> discord.Embed:
        embed = discord.Embed(title="Coming Up...", colour=0x4F0321)
        embed.description = "\n".join(f"`{index}. {title}`" for index, title in enumerate(page, 1))

        return embed

    def is_paginating(self) -> bool:
        # We always want to embed even on 1 page of results...
        return True
