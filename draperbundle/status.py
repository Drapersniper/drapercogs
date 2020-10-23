# -*- coding: utf-8 -*-
from operator import attrgetter
from typing import List

import discord

from redbot.core import commands
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .config_holder import ConfigHolder
from .utilities import get_activity_list

_ = lambda s: s


class MemberStatus(commands.Cog):
    def __init__(self, bot, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = bot
        self.config = ConfigHolder.PlayerStatus

    @commands.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_channels=True, manage_guild=True)
    @commands.bot_has_permissions(embed_links=True)
    async def linkchannel(
        self, ctx: commands.Context, channel: discord.TextChannel, *, game: str = None
    ):
        """Link a channel to a game - Requires exact game name"""
        await self.config.channel(channel).game.set(game)
        await ctx.tick()

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def splaying(self, ctx: commands.Context, *, game: str = None):
        """Shows who's playing what games."""
        game_name = _("what")
        ending = _(" any games.")
        game_list = []
        if game is None:
            game = await self.config.channel(ctx.channel).game()

        if game:
            game_name = game
            game_list = [game]
            ending = f" {game}."
        playing_data = await self.get_players_per_activity(ctx=ctx, game_name=game_list)

        if playing_data:
            embed_list = await get_activity_list(
                ctx, playing_data, game_name, discord.ActivityType.playing
            )
            await menu(
                ctx,
                pages=embed_list,
                controls=DEFAULT_CONTROLS,
                message=None,
                page=0,
                timeout=60,
            )
        else:
            await ctx.maybe_send_embed(
                _("No one is playing{ending}").format(ending=ending)
            )

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def swatching(self, ctx: commands.Context):
        """Shows who's watching what."""

        data = await self.get_players_per_activity(ctx=ctx, movie=True)
        if data:
            embed_list = await get_activity_list(
                ctx, data, None, discord.ActivityType.watching
            )
            await menu(
                ctx,
                pages=embed_list,
                controls=DEFAULT_CONTROLS,
                message=None,
                page=0,
                timeout=60,
            )
        else:
            await ctx.maybe_send_embed(_("No one is watching anything."))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def slistening(self, ctx: commands.Context):
        """Shows who's listening what."""

        data = await self.get_players_per_activity(ctx=ctx, music=True)
        if data:
            embed_list = await get_activity_list(
                ctx, data, None, discord.ActivityType.listening
            )

            await menu(
                ctx,
                pages=embed_list,
                controls=DEFAULT_CONTROLS,
                message=None,
                page=0,
                timeout=60,
            )

        else:
            await ctx.maybe_send_embed(_("No one is listening to anything."))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def sstreaming(self, ctx: commands.Context, *, game: str = None):
        """Shows who's streaming what games."""
        game_name = _("what")
        ending = "."
        game_list = []
        if game is None:
            game = await self.config.channel(ctx.channel).game()
        if game:
            game_name = game
            game_list = [game]
            ending = f" {game}."
        streaming_data = await self.get_players_per_activity(
            ctx=ctx, stream=True, game_name=game_list
        )
        if streaming_data:
            embed_list = await get_activity_list(
                ctx, streaming_data, game_name, discord.ActivityType.streaming
            )

            await menu(
                ctx,
                pages=embed_list,
                controls=DEFAULT_CONTROLS,
                message=None,
                page=0,
                timeout=60,
            )
        else:
            await ctx.maybe_send_embed(
                _("No one is streaming{ending}").format(ending=ending)
            )

    @staticmethod
    async def get_players_per_activity(
        ctx: commands.Context,
        stream: bool = False,
        music: bool = False,
        movie: bool = None,
        game_name: List[str] = None,
    ):
        looking_for = discord.ActivityType.playing
        name_property = "name"
        if stream:
            looking_for = discord.ActivityType.streaming
            name_property = "details"
        elif music:
            looking_for = discord.ActivityType.listening
            name_property = "title"
        elif movie:
            looking_for = discord.ActivityType.watching
            name_property = "name"

        member_data_new = {}
        for member in ctx.guild.members:
            if member.activities:
                interested_in = [
                    activity
                    for activity in member.activities
                    if activity and activity.type == looking_for
                ]
                if interested_in and not member.bot:
                    game = getattr(interested_in[0], name_property, None)
                    if game:
                        if (
                            game_name
                            and game not in game_name
                            and not any(g.lower() in game.lower() for g in game_name)
                        ):
                            continue
                        if looking_for in [
                            discord.ActivityType.playing,
                            discord.ActivityType.streaming,
                        ]:
                            publisher = (
                                await ConfigHolder.PublisherManager.publisher.get_raw()
                            )
                            publisher = publisher.get(game)
                        elif looking_for == discord.ActivityType.watching:
                            publisher = "movie"
                        else:
                            publisher = "spotify"
                        accounts = (
                            await ConfigHolder.AccountManager.user(member).get_raw()
                        ).get("account", {})
                        account = accounts.get(publisher)
                        if not account:
                            account = None

                        hoisted_roles = [r for r in member.roles if r and r.hoist]
                        top_role = max(
                            hoisted_roles,
                            key=attrgetter("position"),
                            default=member.top_role,
                        )
                        role_value = top_role.position * -1
                        if game in member_data_new:
                            member_data_new[game].append(
                                (member.mention, str(member), role_value, account)
                            )
                        else:
                            member_data_new[game] = [
                                (member.mention, str(member), role_value, account)
                            ]
        return member_data_new
