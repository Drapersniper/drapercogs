# -*- coding: utf-8 -*-
# Standard Library
import logging
import math
import random
import re

# Cog Dependencies
import discord
import wavelink

from discord.ext import menus
from redbot.core import commands

# Cog Relative Imports
from ... import errors
from ...UX import PaginatorSource
from ...abc import MixinMeta
from ...classes.meta import CompositeMetaClass
from ...utilities.wavelink import Player, Track

__log__ = logging.getLogger("red.cogs.Audio.cog.Commands.player_controller")


class PlayerControllerCommands(MixinMeta, metaclass=CompositeMetaClass):
    @commands.command()
    async def connect(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        """Connect to a voice channel."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if player.is_connected:
            return

        channel = getattr(ctx.author.voice, "channel", channel)
        if channel is None:
            raise errors.NoChannelProvided

        await player.connect(channel.id)

    @commands.command()
    async def play(self, ctx: commands.Context, *, query: str):
        """Play or queue a song with the given query."""
        URL_REG = re.compile(r"https?://(?:www\.)?.+")
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            await ctx.invoke(self.connect)

        query = query.strip("<>")
        if not URL_REG.match(query):
            query = f"ytsearch:{query}"

        tracks = await self.bot.wavelink.get_tracks(query)
        if not tracks:
            return await ctx.send(
                "No songs were found with that query. Please try again.", delete_after=15
            )

        if isinstance(tracks, wavelink.TrackPlaylist):
            for track in tracks.tracks:
                track = Track(track.id, track.info, requester=ctx.author)
                await player.queue.put(track)

            await ctx.send(
                f'```ini\nAdded the playlist {tracks.data["playlistInfo"]["name"]}'
                f" with {len(tracks.tracks)} songs to the queue.\n```",
                delete_after=15,
            )
        else:
            track = Track(tracks[0].id, tracks[0].info, requester=ctx.author)
            await ctx.send(f"```ini\nAdded {track.title} to the Queue\n```", delete_after=15)
            await player.queue.put(track)

        if not player.is_playing:
            await player.do_next()

    @commands.command()
    async def pause(self, ctx: commands.Context):
        """Pause the currently playing song."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has paused the player.", delete_after=10)
            player.votes.pause.clear()

            return await player.set_pause(True)

        required = self.get_votes_required(ctx)
        player.votes.pause.add(ctx.author.id)

        if player.pause_votes >= required:
            await ctx.send("Vote to pause passed. Pausing player.", delete_after=10)
            player.votes.pause.clear()
            await player.set_pause(True)
        else:
            await ctx.send(f"{ctx.author.mention} has voted to pause the player.", delete_after=15)

    @commands.command()
    async def resume(self, ctx: commands.Context):
        """Resume a currently paused player."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_paused or not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has resumed the player.", delete_after=10)
            player.votes.resume.clear()

            return await player.set_pause(False)

        required = self.get_votes_required(ctx)
        player.votes.resume.add(ctx.author.id)

        if player.resume_votes >= required:
            await ctx.send("Vote to resume passed. Resuming player.", delete_after=10)
            player.votes.resume.clear()
            await player.set_pause(False)
        else:
            await ctx.send(
                f"{ctx.author.mention} has voted to resume the player.", delete_after=15
            )

    @commands.command()
    async def skip(self, ctx: commands.Context):
        """Skip the currently playing song."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has skipped the song.", delete_after=10)
            player.votes.skip.clear()

            return await player.stop()

        if ctx.author == player.current.requester:
            await ctx.send("The song requester has skipped the song.", delete_after=10)
            player.votes.skip.clear()

            return await player.stop()

        required = self.get_votes_required(ctx)
        player.votes.skip.add(ctx.author.id)

        if player.skip_votes >= required:
            await ctx.send("Vote to skip passed. Skipping song.", delete_after=10)
            player.votes.skip.clear()
            await player.stop()
        else:
            await ctx.send(f"{ctx.author.mention} has voted to skip the song.", delete_after=15)

    @commands.command()
    async def stop(self, ctx: commands.Context):
        """Stop the player and clear all internal states."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has stopped the player.", delete_after=10)
            return await player.teardown()

        required = self.get_votes_required(ctx)
        player.votes.stop.add(ctx.author.id)

        if player.stop_votes >= required:
            await ctx.send("Vote to stop passed. Stopping the player.", delete_after=10)
            await player.teardown()
        else:
            await ctx.send(f"{ctx.author.mention} has voted to stop the player.", delete_after=15)

    @commands.command(aliases=["v", "vol"])
    async def volume(self, ctx: commands.Context, *, vol: int):
        """Change the players volume, between 1 and 100."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the volume.")

        if not 0 < vol < 101:
            return await ctx.send("Please enter a value between 1 and 100.")

        await player.set_volume(vol)
        await ctx.send(f"Set the volume to **{vol}**%", delete_after=7)

    @commands.command(aliases=["mix"])
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the players queue."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if player.queue.qsize() < 3:
            return await ctx.send("Add more songs to the queue before shuffling.", delete_after=15)

        if self.is_privileged(ctx):
            await ctx.send("An admin or DJ has shuffled the playlist.", delete_after=10)
            player.votes.shuffle.clear()
            return random.shuffle(player.queue._queue)

        required = self.get_votes_required(ctx)
        player.votes.shuffle.add(ctx.author.id)

        if player.shuffle_votes >= required:
            await ctx.send("Vote to shuffle passed. Shuffling the playlist.", delete_after=10)
            player.votes.shuffle.clear()
            random.shuffle(player.queue._queue)
        else:
            await ctx.send(
                f"{ctx.author.mention} has voted to shuffle the playlist.", delete_after=15
            )

    @commands.command(hidden=True)
    async def vol_up(self, ctx: commands.Context):
        """Command used for volume up button."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume + 10) / 10)) * 10

        if vol > 100:
            vol = 100
            await ctx.send("Maximum volume reached", delete_after=7)

        await player.set_volume(vol)

    @commands.command(hidden=True)
    async def vol_down(self, ctx: commands.Context):
        """Command used for volume down button."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected or not self.is_privileged(ctx):
            return

        vol = int(math.ceil((player.volume - 10) / 10)) * 10

        if vol < 0:
            vol = 0
            await ctx.send("Player is currently muted", delete_after=10)

        await player.set_volume(vol)

    @commands.command(aliases=["eq"])
    async def equalizer(self, ctx: commands.Context, *, equalizer: str):
        """Change the players equalizer."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only the DJ or admins may change the equalizer.")

        eqs = {
            "flat": wavelink.Equalizer.flat(),
            "boost": wavelink.Equalizer.boost(),
            "metal": wavelink.Equalizer.metal(),
            "piano": wavelink.Equalizer.piano(),
        }

        eq = eqs.get(equalizer.lower(), None)

        if not eq:
            joined = "\n".join(eqs.keys())
            return await ctx.send(f"Invalid EQ provided. Valid EQs:\n\n{joined}")

        await ctx.send(f"Successfully changed equalizer to {equalizer}", delete_after=15)
        await player.set_eq(eq)

    @commands.command(aliases=["q", "que"])
    async def queue(self, ctx: commands.Context):
        """Display the players queued songs."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if player.queue.qsize() == 0:
            return await ctx.send("There are no more songs in the queue.", delete_after=15)

        entries = [track.title for track in player.queue._queue]
        pages = PaginatorSource(entries=entries)
        paginator = menus.MenuPages(source=pages, timeout=None, delete_message_after=True)

        await paginator.start(ctx)

    @commands.command(aliases=["np", "now_playing", "current"])
    async def nowplaying(self, ctx: commands.Context):
        """Update the player controller."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        await player.invoke_controller()

    @commands.command(aliases=["swap"])
    async def swap_dj(self, ctx: commands.Context, *, member: discord.Member = None):
        """Swap the current DJ to another member in the voice channel."""
        player: Player = self.bot.wavelink.get_player(
            guild_id=ctx.guild.id, cls=Player, context=ctx
        )

        if not player.is_connected:
            return

        if not self.is_privileged(ctx):
            return await ctx.send("Only admins and the DJ may use this command.", delete_after=15)

        members = self.bot.get_channel(int(player.channel_id)).members

        if member and member not in members:
            return await ctx.send(
                f"{member} is not currently in voice, so can not be a DJ.", delete_after=15
            )

        if member and member == player.dj:
            return await ctx.send("Cannot swap DJ to the current DJ... :)", delete_after=15)

        if len(members) <= 2:
            return await ctx.send("No more members to swap to.", delete_after=15)

        if member:
            player.dj = member
            return await ctx.send(f"{member.mention} is now the DJ.")

        for m in members:
            if m == player.dj or m.bot:
                continue
            else:
                player.dj = m
                return await ctx.send(f"{member.mention} is now the DJ.")
