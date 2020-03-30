import logging

import lavalink

from redbot.core import commands

from ..abc import MixinMeta
from ..cog_utils import CompositeMetaClass, _

log = logging.getLogger("red.cogs.Audio.cog.Commands.Martine")


class MartineCommands(MixinMeta, metaclass=CompositeMetaClass):
    @commands.command(name="playskip", aliases=["psk"])
    @commands.bot_has_permissions(embed_links=True)
    async def command_playskip(self, ctx: commands.Context, *, query: str):
        """Play and skip."""
        await ctx.invoke(self.command_bumpplay, play_now=True, query=query)

    @commands.command(aliases=["cl"])
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def command_clear(self, ctx: commands.Context):
        """Clear the queue."""
        await ctx.invoke(self.command_queue_clear)

    @commands.is_owner()
    @commands.command(name="disconnectplayers", aliases=["dcplay"])
    @commands.guild_only()
    async def command_disconnectplayers(self, ctx):
        """Disconnect from all non-playing voice channels."""
        stopped_players = [p for p in lavalink.all_players() if p.current is None]
        for player in stopped_players:
            await player.disconnect()
            self.api_interface.persistent_queue_api.drop(player.channel.guild.id)
        await ctx.tick()
        return await self.send_embed_msg(
            ctx,
            title=_("Admin action"),
            description=_("Successfully disconnected from all non-playing voice channels."),
            success=True,
        )

    @commands.is_owner()
    @commands.command(name="disconnectallplayers", aliases=["dcallplay"])
    @commands.guild_only()
    async def command_disconnectallplayers(self, ctx):
        """Disconnect all Lavalink players."""
        for player in lavalink.all_players():
            await player.disconnect()
            self.api_interface.persistent_queue_api.drop(player.channel.guild.id)
        await ctx.tick()
        return await self.send_embed_msg(
            ctx,
            title=_("Admin action"),
            description=_("Successfully disconnected from all voice channels."),
            success=True,
        )
