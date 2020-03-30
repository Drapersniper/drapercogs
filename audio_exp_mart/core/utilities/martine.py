import asyncio
import contextlib
import logging
from typing import MutableMapping, Tuple

import discord
import lavalink

from redbot.core import commands
from redbot.core.utils.chat_formatting import box
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate

from ..abc import MixinMeta
from ..cog_utils import COLOUR_RED, CompositeMetaClass, _

log = logging.getLogger("red.cogs.Audio.cog.Utilities.Martine")


class MartineUtilities(MixinMeta, metaclass=CompositeMetaClass):
    async def make_now_embed(
        self, player: lavalink.Player, ctx: commands.Context
    ) -> discord.Embed:
        if player.current:
            arrow = await self.draw_time(ctx)
            pos = lavalink.utils.format_time(player.position)
            if player.current.is_stream:
                dur = "\N{LARGE RED CIRCLE} LIVE"
            else:
                dur = lavalink.utils.format_time(player.current.length)
            song = await self.get_track_description(player.current, self.local_folder_current_path)
            song += _("\nRequested by: **{track.requester}**")
            song += "\n\n{arrow}`{pos} / {dur}`"
            song = song.format(track=player.current, arrow=arrow, pos=pos, dur=dur)
        else:
            song = _("Nothing.")

        volume = await self.config.guild(ctx.guild).volume()
        embed = discord.Embed(
            color=await ctx.embed_colour(), description=song + f"\n\nVolume: `{volume}%`"
        )
        embed.set_author(
            name="Now Playing", icon_url="https://cdn.discordapp.com/emojis/528753381418860595.gif"
        )

        if await self.config.guild(ctx.guild).thumbnail() and player.current:
            if player.current.thumbnail:
                embed.set_thumbnail(url=player.current.thumbnail)

        shuffle = await self.config.guild(ctx.guild).shuffle()
        repeat = await self.config.guild(ctx.guild).repeat()
        autoplay = await self.config.guild(ctx.guild).auto_play()
        text = ""
        text += (
            _("Auto-Play")
            + ": "
            + ("\N{WHITE HEAVY CHECK MARK}" if autoplay else "\N{CROSS MARK}")
        )
        text += (
            (" | " if text else "")
            + _("Shuffle")
            + ": "
            + ("\N{WHITE HEAVY CHECK MARK}" if shuffle else "\N{CROSS MARK}")
        )
        text += (
            (" | " if text else "")
            + _("Repeat")
            + ": "
            + ("\N{WHITE HEAVY CHECK MARK}" if repeat else "\N{CROSS MARK}")
        )
        embed.set_footer(text=text)

        return embed

    async def make_now_task(
        self,
        ctx: commands.Context,
        player: lavalink.Player,
        message: discord.Message,
        expected_emoji: Tuple[str, ...],
        emoji: MutableMapping[str, str],
        timeout: float = 30.0,
    ) -> None:
        while True:
            try:
                if player.current:
                    task = start_adding_reactions(message, expected_emoji)
                else:
                    task = None

                try:
                    (r, u) = await self.bot.wait_for(
                        "reaction_add",
                        check=ReactionPredicate.with_emojis(expected_emoji, message),
                        timeout=timeout,
                    )
                except asyncio.TimeoutError:
                    await self._clear_react(message, emoji)
                    return
                else:
                    if task is not None:
                        task.cancel()
                reacts = {v: k for k, v in emoji.items()}
                react = reacts[r.emoji]
                ctx.author = ctx.guild.get_member(u.id)
                if react == "prev":
                    await ctx.invoke(self.command_hidden_prev)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "stop":
                    await ctx.invoke(self.command_hidden_stop)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "pause":
                    await ctx.invoke(self.command_hidden_pause)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "next":
                    await ctx.invoke(self.command_hidden_skip)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "vol_up":
                    vol = await self.config.guild(ctx.guild).volume()
                    await ctx.invoke(self.command_hidden_volume, vol=vol + 10)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "vol_down":
                    vol = await self.config.guild(ctx.guild).volume()
                    await ctx.invoke(self.command_hidden_volume, vol=vol - 10)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "queue":
                    await ctx.invoke(self.command_queue)
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                elif react == "refresh":
                    await self.update_now_embed(player, ctx, message)
                    await self.remove_react(message, r, u)
                await asyncio.sleep(4)
            except Exception as error:
                log.error(error)
                channel = self.bot.get_channel(540710309271306270)
                await channel.send("**Error in `_now_task` function:**" + box(str(error)))
                continue

    async def update_now_embed(
        self, player: lavalink.Player, ctx: commands.Context, message: discord.Message
    ) -> None:
        new_embed = await self.make_now_embed(player, ctx)
        with contextlib.suppress(discord.HTTPException):
            await message.edit(embed=new_embed)

    async def delete_message_after(self, msg: discord.Message, delay: int = 4) -> None:
        await msg.delete(delay=delay)

    async def special_skip(self, ctx: commands.Context, skip_to_track: int = None):
        player = lavalink.get_player(ctx.guild.id)
        autoplay = await self.config.guild(player.channel.guild).auto_play()
        if not player.current or (not player.queue and not autoplay):
            try:
                pos, dur = player.position, player.current.length
            except AttributeError:
                msg = await self.send_embed_msg(ctx, title=_("There's nothing in the queue."))
                await self.delete_message_after(msg)
                return
            time_remain = lavalink.utils.format_time(dur - pos)
            if player.current.is_stream:
                embed = discord.Embed(colour=COLOUR_RED, title=_("There's nothing in the queue."))
                embed.set_footer(
                    text=_("\N{LARGE RED CIRCLE} Currently livestreaming {track}").format(
                        track=player.current.title
                    )
                )
            else:
                embed = discord.Embed(title=_("There's nothing in the queue."))
                embed.set_footer(
                    text=_("{time} left on {track}").format(
                        time=time_remain, track=player.current.title
                    )
                )
            msg = await self.send_embed_msg(ctx, embed=embed)
            await self.delete_message_after(msg)
            return
        elif autoplay and not player.queue:
            embed = discord.Embed(
                title=_("⏩ Track Skipped"),
                description=await self.get_track_description(
                    player.current, self.local_folder_current_path
                ),
            )
            msg = await self.send_embed_msg(ctx, embed=embed)
            await self.delete_message_after(msg)
            return await player.skip()

        queue_to_append = []
        if skip_to_track is not None and skip_to_track != 1:
            if skip_to_track < 1:
                msg = await self.send_embed_msg(
                    ctx, title=_("Track number must be equal to or greater than 1."), error=True,
                )
                await self.delete_message_after(msg)
                return
            elif skip_to_track > len(player.queue):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_(
                        "There are only {queuelen} songs currently queued.".format(
                            queuelen=len(player.queue)
                        )
                    ),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
            embed = discord.Embed(
                title=_("⏩ {skip_to_track} Tracks Skipped".format(skip_to_track=skip_to_track))
            )
            msg = await self.send_embed_msg(ctx, embed=embed)
            if player.repeat:
                queue_to_append = player.queue[0 : min(skip_to_track - 1, len(player.queue) - 1)]
            player.queue = player.queue[
                min(skip_to_track - 1, len(player.queue) - 1) : len(player.queue)
            ]
        else:
            embed = discord.Embed(
                title=_("⏩ Track Skipped"),
                description=await self.get_track_description(
                    player.current, self.local_folder_current_path
                ),
            )
            msg = await self.send_embed_msg(ctx, embed=embed)
        self.bot.dispatch("red_audio_skip_track", player.channel.guild, player.current, ctx.author)
        await player.play()
        player.queue += queue_to_append
        await self.delete_message_after(msg)

    def get_cross_emoji(self, ctx: commands.Context) -> str:
        if ctx.me.permissions_in(ctx.channel).external_emojis:
            cross = discord.utils.get(self.bot.emojis, id=631530205495689236)
        else:
            cross = "\N{CROSS MARK}"
        return cross

    def get_wave_emoji(self, ctx: commands.Context) -> str:
        if ctx.me.permissions_in(ctx.channel).external_emojis:
            emoji = discord.utils.get(self.bot.emojis, id=672268771133489202)
        else:
            emoji = "\N{WAVING HAND SIGN}"
        return emoji
