import discord
from discord.ext.commands import BadArgument
from redbot.core import commands


class ConvertMember(commands.MemberConverter):
    """Converts to a :class:`Member`.

    All lookups are via the local guild. If in a DM context, then the lookup
    is done by the global cache.

    The lookup strategy is as follows (in order):

    1. Lookup by ID.
    2. Lookup by mention.
    3. Lookup by name#discrim
    4. Lookup by name
    5. Lookup by nickname
    6. Lookup by name lower in arg lower
    7. Lookup by nickname lower in arg lower
    """

    async def convert(self, ctx, argument):
        try:
            member = await super().convert(ctx, argument)
        except commands.BadArgument:
            member = discord.utils.find(
                lambda x: argument.lower() in x.name.lower(), ctx.guild.members
            )
            if member is None:
                member = discord.utils.find(
                    lambda x: argument.lower() in x.display_name.lower(),
                    ctx.guild.members,
                )
            if member is None:
                raise BadArgument(f'Member "{argument}" was not found')
        return member
