# -*- coding: utf-8 -*-
# Standard Library
from copy import copy
from operator import attrgetter, itemgetter
from typing import List

# Cog Dependencies
import discord

from redbot.core import commands
from redbot.core.utils.chat_formatting import pagify
from redbot.core.utils.menus import DEFAULT_CONTROLS, menu

from .config_holder import ConfigHolder

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
        embed_colour = await ctx.embed_colour()
        if playing_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(playing_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(
                        title=_("Who's playing {name}?").format(name=game_name),
                        colour=embed_colour,
                    )

                title = "{key} ({value} {status})".format(
                    key=key, value=len(value), status=_("playing")
                )
                content = ""
                for mention, display_name, black_hole, account in sorted(
                    value, key=itemgetter(2, 1)
                ):
                    content += f"{display_name}"
                    if account:
                        content += f" | {account}"
                    content += "\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = "{key} ({extra} {value})".format(
                            key=key, value=enum_count, extra=_("Part")
                        )
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )
        else:
            await ctx.maybe_send_embed(_("No one is playing{ending}").format(ending=ending))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def swatching(self, ctx: commands.Context):
        """Shows who's watching what."""

        watching_data = await self.get_players_per_activity(ctx=ctx, movie=True)
        embed_colour = await ctx.embed_colour()
        if watching_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(watching_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(title=_("Who's watching what?"), colour=embed_colour)

                title = "{key} ({value} {status})".format(
                    key=key, value=len(value), status=_("watching")
                )
                content = ""
                for mention, display_name, black_hole, account in sorted(
                    value, key=itemgetter(2, 1)
                ):
                    content += f"{display_name}"
                    if account:
                        content += f" | {account}"
                    content += "\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = "{key} ({extra} {value})".format(
                            key=key, value=enum_count, extra=_("Part")
                        )
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )
        else:
            await ctx.maybe_send_embed(_("No one is watching anything."))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def slistening(self, ctx: commands.Context):
        """Shows who's listening what."""

        listening_data = await self.get_players_per_activity(ctx=ctx, music=True)
        embed_colour = await ctx.embed_colour()
        if listening_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(listening_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(title=_("Who's listening to what?"), colour=embed_colour)

                title = "{key} ({value} {status})".format(
                    key=key, value=len(value), status=_("listening")
                )
                content = ""
                for mention, display_name, black_hole, account in sorted(
                    value, key=itemgetter(2, 1)
                ):
                    content += f"{display_name}"
                    if account:
                        content += f" | {account}"
                    content += "\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = "{key} ({extra} {value})".format(
                            key=key, value=enum_count, extra=_("Part")
                        )
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )

        else:
            await ctx.maybe_send_embed(_("No one is listening to anything."))

    @commands.command()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def sstreaming(self, ctx: commands.Context, *, game=None):
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
        embed_colour = await ctx.embed_colour()
        if streaming_data:
            embed_list = []
            count = -1
            splitter = 1
            for key, value in sorted(streaming_data.items()):
                count += 1
                if count % splitter == 0:
                    embed = discord.Embed(
                        title=_("Who's streaming {}?").format(game_name), colour=embed_colour
                    )

                title = "{key} ({value} {status})".format(
                    key=key, value=len(value), status=_("streaming")
                )
                content = ""
                for mention, display_name, black_hole, account in sorted(
                    value, key=itemgetter(2, 1)
                ):
                    content += f"{display_name}"
                    if account:
                        content += f" | {account}"
                    content += "\n"

                outputs = pagify(content, page_length=1000, priority=True)
                for enum_count, field in enumerate(outputs, 1):
                    if enum_count > 1:
                        title = "{key} ({extra} {value})".format(
                            key=key, value=enum_count, extra=_("Part")
                        )
                    embed.add_field(name=f"{title}", value=field)
                if count % splitter == 0:
                    embed_list.append(copy(embed))

            await menu(
                ctx, pages=embed_list, controls=DEFAULT_CONTROLS, message=None, page=0, timeout=60
            )
        else:
            await ctx.maybe_send_embed(_("No one is streaming{ending}").format(ending=ending))

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
                            publisher = await ConfigHolder.PublisherManager.publisher.get_raw()
                            publisher = publisher.get(game)
                        elif looking_for == discord.ActivityType.watching:
                            publisher = "movie"
                        else:
                            publisher = "spotify"
                        accounts = (await ConfigHolder.AccountManager.user(member).get_raw()).get(
                            "account", {}
                        )
                        account = accounts.get(publisher)
                        if not account:
                            account = None

                        hoisted_roles = [r for r in member.roles if r and r.hoist]
                        top_role = max(
                            hoisted_roles, key=attrgetter("position"), default=member.top_role
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
