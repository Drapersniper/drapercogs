import asyncio
import contextlib
import logging
import math

import discord
import lavalink

from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_number
from redbot.core.utils.menus import close_menu, menu, next_page, prev_page

from ..abc import MixinMeta
from ..cog_utils import CompositeMetaClass, _

log = logging.getLogger("red.cogs.Audio.cog.Commands.equalizer")


class HiddenCommands(MixinMeta, metaclass=CompositeMetaClass):
    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def command_hidden_pause(self, ctx: commands.Context):
        """Pause or resume a playing track."""
        dj_enabled = self._dj_status_cache.setdefault(
            ctx.guild.id, await self.config.guild(ctx.guild).dj_enabled()
        )
        if not self._player_check(ctx):
            msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
            await self.delete_message_after(msg)
            return
        player = lavalink.get_player(ctx.guild.id)
        if (
            not ctx.author.voice or ctx.author.voice.channel != player.channel
        ) and not await self._can_instaskip(ctx, ctx.author):
            msg = await self.send_embed_msg(
                ctx,
                title=_("Unable To Manage Tracks"),
                description=_("You must be in the voice channel to pause or resume."),
                error=True,
            )
            await self.delete_message_after(msg)
            return
        if dj_enabled:
            if not await self._can_instaskip(
                ctx, ctx.author
            ) and not await self.is_requester_alone(ctx):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Manage Tracks"),
                    description=_("You need the DJ role to pause or resume tracks."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return

        if not player.current:
            msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
            await self.delete_message_after(msg)
            return
        description = await self.get_track_description(
            player.current, self.local_folder_current_path
        )

        if player.current and not player.paused:
            await player.pause()
            msg = await self.send_embed_msg(
                ctx, title=_("⏸ Track Paused"), description=description
            )
            await self.delete_message_after(msg)
            return
        if player.current and player.paused:
            await player.pause(False)
            msg = await self.send_embed_msg(
                ctx, title=_("▶️ Track Resumed"), description=description
            )
            await self.delete_message_after(msg)
            return

        msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
        await self.delete_message_after(msg)

    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def command_hidden_prev(self, ctx: commands.Context):
        """Skip to the start of the previously played track."""
        if not self._player_check(ctx):
            msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
            await self.delete_message_after(msg)
            return
        dj_enabled = self._dj_status_cache.setdefault(
            ctx.guild.id, await self.config.guild(ctx.guild).dj_enabled()
        )
        player = lavalink.get_player(ctx.guild.id)
        if dj_enabled:
            if not await self._can_instaskip(
                ctx, ctx.author
            ) and not await self.is_requester_alone(ctx):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Play Tracks"),
                    description=_("You need the DJ role to skip tracks."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
        if (
            not ctx.author.voice or ctx.author.voice.channel != player.channel
        ) and not await self._can_instaskip(ctx, ctx.author):
            msg = await self.send_embed_msg(
                ctx,
                title=_("Unable To Play Tracks"),
                description=_("You must be in the voice channel to skip the music."),
                error=True,
            )
            await self.delete_message_after(msg)
            return
        if player.fetch("prev_song") is None:
            msg = await self.send_embed_msg(
                ctx,
                title=_("Unable To Play Tracks"),
                description=_("No previous track."),
                error=True,
            )
            await self.delete_message_after(msg)
            return
        else:
            track = player.fetch("prev_song")
            player.add(player.fetch("prev_requester"), track)
            self.bot.dispatch("red_audio_track_enqueue", player.channel.guild, track, ctx.author)
            queue_len = len(player.queue)
            bump_song = player.queue[-1]
            player.queue.insert(0, bump_song)
            player.queue.pop(queue_len)
            await player.skip()
            description = await self.get_track_description(
                player.current, self.local_folder_current_path
            )
            embed = discord.Embed(title=_("◀️ Replaying Track"), description=description)
            msg = await self.send_embed_msg(ctx, embed=embed)
            await self.delete_message_after(msg)

    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True, add_reactions=True)
    async def command_hidden_queue(self, ctx: commands.Context, *, page: int = 1):
        """List the songs in the queue."""

        async def _queue_menu(
            ctx: commands.Context,
            pages: list,
            controls: dict,
            message: discord.Message,
            page: int,
            timeout: float,
            emoji: str,
        ):
            if message:
                await ctx.send_help(self.command_queue)
                with contextlib.suppress(discord.HTTPException):
                    await message.delete()
                return None

        queue_controls = {
            "◀": prev_page,
            self.get_cross_emoji(ctx): close_menu,
            "▶": next_page,
            "\N{INFORMATION SOURCE}": _queue_menu,
        }

        if not self._player_check(ctx):
            msg = await self.send_embed_msg(
                ctx, title=_("There's nothing in the queue."), error=True
            )
            await self.delete_message_after(msg)
            return
        player = lavalink.get_player(ctx.guild.id)
        if player.current and not player.queue:
            arrow = await self.draw_time(ctx)
            pos = lavalink.utils.format_time(player.position)
            if player.current.is_stream:
                dur = "\N{LARGE RED CIRCLE} LIVE"
            else:
                dur = lavalink.utils.format_time(player.current.length)
            song = await self.get_track_description(player.current, self.local_folder_current_path)
            song += _("\n Requested by: **{track.requester}**")
            song += "\n\n{arrow}`{pos}`/`{dur}`"
            song = song.format(track=player.current, arrow=arrow, pos=pos, dur=dur)
            embed = discord.Embed(colour=await ctx.embed_colour(), description=song)
            embed.set_author(
                name="Now Playing",
                icon_url="https://cdn.discordapp.com/emojis/528753381418860595.gif",
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

            msg = await ctx.send(embed=embed)
            await self.delete_message_after(msg)
            return
        elif not player.current and not player.queue:
            msg = await self.send_embed_msg(
                ctx, title=_("There's nothing in the queue."), error=True
            )
            await self.delete_message_after(msg)
            return

        async with ctx.typing():
            limited_queue = player.queue[:500]  # TODO: Improve when Toby menu's are merged
            len_queue_pages = math.ceil(len(limited_queue) / 10)
            queue_page_list = []
            for page_num in range(1, len_queue_pages + 1):
                embed = await self._build_queue_page(ctx, limited_queue, player, page_num)
                queue_page_list.append(embed)
                await asyncio.sleep(0)
            if page > len_queue_pages:
                page = len_queue_pages
        msg = await menu(ctx, queue_page_list, queue_controls, page=(page - 1))
        await self.delete_message_after(msg, 10)
        return

    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def command_hidden_skip(self, ctx: commands.Context, skip_to_track: int = None):
        """Skip to the next track, or to a given track number."""
        if not self._player_check(ctx):
            msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
            await self.delete_message_after(msg)
            return
        player = lavalink.get_player(ctx.guild.id)
        if (
            not ctx.author.voice or ctx.author.voice.channel != player.channel
        ) and not await self._can_instaskip(ctx, ctx.author):
            msg = await self.send_embed_msg(
                ctx,
                title=_("Unable To Skip Tracks"),
                description=_("You must be in the voice channel to skip the music."),
                error=True,
            )
            await self.delete_message_after(msg)
            return
        if not player.current:
            msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
            await self.delete_message_after(msg)
            return
        dj_enabled = self._dj_status_cache.setdefault(
            ctx.guild.id, await self.config.guild(ctx.guild).dj_enabled()
        )
        vote_enabled = await self.config.guild(ctx.guild).vote_enabled()
        is_alone = await self.is_requester_alone(ctx)
        is_requester = await self.is_requester(ctx, ctx.author)
        can_skip = await self._can_instaskip(ctx, ctx.author)

        if dj_enabled and not vote_enabled:
            if not (can_skip or is_requester) and not is_alone:
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Skip Tracks"),
                    description=_(
                        "You need the DJ role or be the track requester to skip tracks."
                    ),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
            if (
                is_requester
                and not can_skip
                and isinstance(skip_to_track, int)
                and skip_to_track > 1
            ):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Skip Tracks"),
                    description=_("You can only skip the current track."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return

        if vote_enabled:
            if not can_skip:
                if skip_to_track is not None:
                    msg = await self.send_embed_msg(
                        ctx,
                        title=_("Unable To Skip Tracks"),
                        description=_(
                            "Can't skip to a specific track in vote mode without the DJ role."
                        ),
                        error=True,
                    )
                    await self.delete_message_after(msg)
                    return
                if ctx.author.id in self.skip_votes[ctx.message.guild]:
                    self.skip_votes[ctx.message.guild].remove(ctx.author.id)
                    reply = _("I removed your vote to skip.")
                else:
                    self.skip_votes[ctx.message.guild].append(ctx.author.id)
                    reply = _("You voted to skip.")

                num_votes = len(self.skip_votes[ctx.message.guild])
                vote_mods = []
                for member in player.channel.members:
                    can_skip = await self._can_instaskip(ctx, member)
                    if can_skip:
                        vote_mods.append(member)
                num_members = len(player.channel.members) - len(vote_mods)
                vote = int(100 * num_votes / num_members)
                percent = await self.config.guild(ctx.guild).vote_percent()
                if vote >= percent:
                    self.skip_votes[ctx.message.guild] = []
                    await self.send_embed_msg(ctx, title=_("Vote threshold met."))
                    return await self.special_skip(ctx)
                else:
                    reply += _(
                        " Votes: {num_votes}/{num_members}"
                        " ({cur_percent}% out of {required_percent}% needed)"
                    ).format(
                        num_votes=humanize_number(num_votes),
                        num_members=humanize_number(num_members),
                        cur_percent=vote,
                        required_percent=percent,
                    )
                    msg = await self.send_embed_msg(ctx, title=reply)
                    await self.delete_message_after(msg, 5)
                    return
            else:
                return await self.special_skip(ctx, skip_to_track)
        else:
            return await self.special_skip(ctx, skip_to_track)

    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def command_hidden_stop(self, ctx: commands.Context):
        """Stop playback and clear the queue."""
        dj_enabled = self._dj_status_cache.setdefault(
            ctx.guild.id, await self.config.guild(ctx.guild).dj_enabled()
        )
        vote_enabled = await self.config.guild(ctx.guild).vote_enabled()
        if not self._player_check(ctx):
            msg = await self.send_embed_msg(ctx, title=_("Nothing playing."), error=True)
            await self.delete_message_after(msg)
            return
        player = lavalink.get_player(ctx.guild.id)
        if (
            not ctx.author.voice or ctx.author.voice.channel != player.channel
        ) and not await self._can_instaskip(ctx, ctx.author):
            msg = await self.send_embed_msg(
                ctx,
                title=_("Unable To Stop Player"),
                description=_("You must be in the voice channel to stop the music."),
                error=True,
            )
            await self.delete_message_after(msg)
            return
        if vote_enabled or vote_enabled and dj_enabled:
            if not await self._can_instaskip(
                ctx, ctx.author
            ) and not await self.is_requester_alone(ctx):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Stop Player"),
                    description=_("There are other people listening - vote to skip instead."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
        if dj_enabled and not vote_enabled:
            if not await self._can_instaskip(ctx, ctx.author):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Stop Player"),
                    description=_("You need the DJ role to stop the music."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
        if (
            player.is_playing
            or (not player.is_playing and player.paused)
            or player.queue
            or getattr(player.current, "extras", {}).get("autoplay")
        ):
            eq = player.fetch("eq")
            if eq:
                await self.config.custom("EQUALIZER", ctx.guild.id).eq_bands.set(eq.bands)
            player.queue = []
            player.store("playing_song", None)
            player.store("prev_requester", None)
            player.store("prev_song", None)
            player.store("requester", None)
            await player.stop()
            msg = await self.send_embed_msg(ctx, title=_("⏹ Stopping..."))
            self.api_interface.persistent_queue_api.drop(ctx.guild.id)
            await self.delete_message_after(msg)

    @commands.command(hidden=True)
    @commands.is_owner()
    @commands.guild_only()
    @commands.bot_has_permissions(embed_links=True)
    async def command_hidden_volume(self, ctx: commands.Context, vol: int = None):
        """Set the volume. Can be between: 1% - 150%."""
        dj_enabled = self._dj_status_cache.setdefault(
            ctx.guild.id, await self.config.guild(ctx.guild).dj_enabled()
        )
        if not vol:
            vol = await self.config.guild(ctx.guild).volume()
            embed = discord.Embed(
                colour=await ctx.embed_colour(), title=f"🔊 Current Volume: `{vol}%`"
            )
            if not self._player_check(ctx):
                embed.set_footer(text=_("Nothing playing."))
            msg = await self.send_embed_msg(ctx, embed=embed)
            await self.delete_message_after(msg)
            return
        if self._player_check(ctx):
            player = lavalink.get_player(ctx.guild.id)
            if (
                not ctx.author.voice or ctx.author.voice.channel != player.channel
            ) and not await self._can_instaskip(ctx, ctx.author):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Change Volume"),
                    description=_("You must be in the voice channel to change the volume."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
        if dj_enabled:
            if not await self._can_instaskip(ctx, ctx.author) and not await self._has_dj_role(
                ctx, ctx.author
            ):
                msg = await self.send_embed_msg(
                    ctx,
                    title=_("Unable To Change Volume"),
                    description=_("You need the DJ role to change the volume."),
                    error=True,
                )
                await self.delete_message_after(msg)
                return
        if vol < 0:
            vol = 0
        if vol > 150:
            vol = 150
            await self.config.guild(ctx.guild).volume.set(vol)
            if self._player_check(ctx):
                await lavalink.get_player(ctx.guild.id).set_volume(vol)
        else:
            await self.config.guild(ctx.guild).volume.set(vol)
            if self._player_check(ctx):
                await lavalink.get_player(ctx.guild.id).set_volume(vol)
        embed = discord.Embed(colour=await ctx.embed_colour(), title=f"🔊 Volume set to: `{vol}%`")
        if not self._player_check(ctx):
            embed.set_footer(text=_("Nothing playing."))
        msg = await self.send_embed_msg(ctx, embed=embed)
        await self.delete_message_after(msg)
