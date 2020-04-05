# -*- coding: utf-8 -*-
# Cog Dependencies
import regex

from discord.ext import commands as dpy_commands


class ConvertUserAPI(dpy_commands.UserConverter):
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
        except dpy_commands.BadArgument:
            user = None
            match = self._get_id_match(argument) or regex.match(r"<@!?([0-9]+)>$", argument)
            if match is not None:
                user_id = int(match.group(1))
                user = await ctx.bot.fetch_user(user_id)
            if user is None:
                raise dpy_commands.BadArgument('User "{}" not found'.format(argument))
        return user
