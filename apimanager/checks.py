from redbot.core import commands

from .api import API


async def is_api_user(ctx: commands.Context):
    api_user = await API.get_user(cog=ctx.cog, member=ctx.author)
    ctx.audio_api_user = api_user
    if not api_user:
        return False
    return api_user.can_read


async def is_not_api_user(ctx: commands.Context):
    api_user = await API.get_user(cog=ctx.cog, member=ctx.author)
    if not api_user:
        return True
    return not api_user.can_read and not (api_user.is_blacklisted or api_user.token)


async def is_api_contributor(ctx: commands.Context):
    api_user = await API.get_user(cog=ctx.cog, member=ctx.author)
    ctx.audio_api_user = api_user
    if not api_user:
        return False
    return api_user.can_post


async def is_api_mod(ctx: commands.Context):
    api_user = await API.get_user(cog=ctx.cog, member=ctx.author)
    ctx.audio_api_user = api_user
    if not api_user:
        return False
    return api_user.can_delete


async def is_api_admin(ctx: commands.Context):
    api_user = await API.get_user(cog=ctx.cog, member=ctx.author)
    ctx.audio_api_user = api_user
    if not api_user:
        return False
    return not api_user.is_blacklisted and (api_user.is_admin or api_user.is_superuser)
