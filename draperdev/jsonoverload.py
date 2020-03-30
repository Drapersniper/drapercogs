# -*- coding: utf-8 -*-
# Cog Dependencies
from redbot.core import Config, commands
from redbot.core.bot import Red

_config_identifier: int = 208903205982044161


class DraperDevJson(commands.Cog):
    """Drapers JSON overload commands."""

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, _config_identifier, force_registration=True)

    def cog_unload(self) -> None:
        from .hackyjson import restore_stdlib

        restore_stdlib()

    @commands.is_owner()
    @commands.group(name="hackydev")
    async def _hackydev(self, ctx: commands.Context):
        """Change hackydev settings."""

    @_hackydev.command(name="overload")
    async def _hackydev_overload(self, ctx: commands.Context):
        """Overload JSON lib."""
        from .hackyjson import overload_stdlib

        overload_stdlib()
        await ctx.tick()

    @_hackydev.command(name="revert")
    async def _hackydev_undo_overload(self, ctx: commands.Context):
        """Revert the JSON lib overload."""
        from .hackyjson import restore_stdlib

        restore_stdlib()
        await ctx.tick()
