# -*- coding: utf-8 -*-
# Standard Library
import re

# Cog Dependencies
from redbot.core import commands


class GuildConverterAPI(commands.Converter):
    async def convert(self, ctx: commands.Context, argument: str):
        guild_raw = argument
        target_guild = None

        if guild_raw.isnumeric():
            guild_raw = int(guild_raw)
            try:
                target_guild = ctx.bot.get_guild(guild_raw)
            except Exception:
                target_guild = None
            guild_raw = str(guild_raw)
        if target_guild is None:
            try:
                target_guild = await commands.GuildConverter.convert(ctx, guild_raw)
            except Exception:
                target_guild = None
        if target_guild is None:
            try:
                target_guild = await ctx.bot.fetch_guild(guild_raw)
            except Exception:
                target_guild = None
        if target_guild is None:
            raise commands.BadArgument(f"Invalid Guild: {argument}")
        return target_guild


class ConvertUserAPI(commands.UserConverter):
    """Converts to a :class:`User`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache, ten as a final resolt the API

    The lookup strategy is as follows (in order):

     1. Lookup by ID.
     2. Lookup by mention.
     3. Lookup by name#discrim
     4. Lookup by name
     5. Looks up by ID through the API
    """

    async def convert(self, ctx, argument):
        try:
            user = await super().convert(ctx, argument)
        except commands.BadArgument:
            user = None
            match = self._get_id_match(argument) or re.match(r"<@!?([0-9]+)>$", argument)
            if match is not None:
                user_id = int(match.group(1))
                user = await ctx.bot.fetch_user(user_id)
            if user is None:
                raise commands.BadArgument('User "{}" not found'.format(argument))
        return user
