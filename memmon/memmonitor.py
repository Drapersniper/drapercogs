from __future__ import annotations
import concurrent
import contextlib
import linecache
import logging
import os
import tracemalloc
import platform
import asyncio
from typing import Iterable

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import pagify

if platform.system() == "Windows":
    raise RuntimeError("Cannot use this cog on Windows")

tracemalloc.start()
_SEND_MESSAGE = ""
log = logging.getLogger("red.MEMMonitor")


class AsyncSnapshot(tracemalloc.Snapshot):
    def __init__(self, traces, traceback_limit):
        super().__init__(traces, traceback_limit)

    async def _filter_trace(self, include_filters, exclude_filters, trace) -> bool:
        if include_filters:
            if not any(
                [
                    trace_filter._match(trace)
                    async for trace_filter in AsyncIter(include_filters, steps=5)
                ]
            ):
                return False
        if exclude_filters:
            if any(
                [
                    not trace_filter._match(trace)
                    async for trace_filter in AsyncIter(exclude_filters, steps=5)
                ]
            ):
                return False
        return True

    async def filter_traces(self, filters) -> AsyncSnapshot:
        """
        Create a new Snapshot instance with a filtered traces sequence, filters
        is a list of Filter or DomainFilter instances.  If filters is an empty
        list, return a new Snapshot instance with a copy of the traces.
        """
        if not isinstance(filters, Iterable):
            raise TypeError("filters must be a list of filters, not %s" % type(filters).__name__)

        if filters:
            include_filters = []
            exclude_filters = []
            async for trace_filter in AsyncIter(filters, steps=5):
                if trace_filter.inclusive:
                    include_filters.append(trace_filter)
                else:
                    exclude_filters.append(trace_filter)
            total_traces = len(self.traces._traces)
            new_traces = [
                trace
                async for trace in AsyncIter(
                    self.traces._traces, steps=int(total_traces * 0.01), delay=1.0
                )
                if await self._filter_trace(include_filters, exclude_filters, trace)
            ]
        else:
            new_traces = self.traces._traces.copy()
        return AsyncSnapshot(new_traces, self.traceback_limit)

    async def _async_group_by(self, key_type, cumulative):
        if key_type not in ("traceback", "filename", "lineno"):
            raise ValueError("unknown key_type: %r" % (key_type,))
        if cumulative and key_type not in ("lineno", "filename"):
            raise ValueError("cumulative mode cannot by used " "with key type %r" % key_type)

        stats = {}
        tracebacks = {}
        if not cumulative:
            total_traces = len(self.traces._traces)
            async for trace in AsyncIter(
                self.traces._traces, steps=int(total_traces * 0.01), delay=0.5
            ):
                domain, size, trace_traceback = trace
                try:
                    traceback = tracebacks[trace_traceback]
                except KeyError:
                    if key_type == "traceback":
                        frames = trace_traceback
                    elif key_type == "lineno":
                        frames = trace_traceback[:1]
                    else:  # key_type == 'filename':
                        frames = ((trace_traceback[0][0], 0),)
                    traceback = tracemalloc.Traceback(frames)
                    tracebacks[trace_traceback] = traceback
                try:
                    stat = stats[traceback]
                    stat.size += size
                    stat.count += 1
                except KeyError:
                    stats[traceback] = tracemalloc.Statistic(traceback, size, 1)
        else:
            # cumulative statistics
            total_traces = len(self.traces._traces)
            async for trace in AsyncIter(
                self.traces._traces, steps=int(total_traces * 0.01), delay=0.5
            ):
                domain, size, trace_traceback = trace
                total_frame = len(trace_traceback)
                async for frame in AsyncIter(
                    trace_traceback, steps=int(total_frame * 0.01), delay=0.5
                ):
                    try:
                        traceback = tracebacks[frame]
                    except KeyError:
                        if key_type == "lineno":
                            frames = (frame,)
                        else:  # key_type == 'filename':
                            frames = ((frame[0], 0),)
                        traceback = tracemalloc.Traceback(frames)
                        tracebacks[frame] = traceback
                    try:
                        stat = stats[traceback]
                        stat.size += size
                        stat.count += 1
                    except KeyError:
                        stats[traceback] = tracemalloc.Statistic(traceback, size, 1)
        return stats

    async def statistics(self, key_type, cumulative=False):
        """
        Group statistics by key_type. Return a sorted list of Statistic
        instances.
        """
        grouped = await self._async_group_by(key_type, cumulative)
        statistics = list(grouped.values())
        statistics.sort(reverse=True, key=tracemalloc.Statistic._sort_key)
        return statistics

    @classmethod
    def from_sync(cls, snap: tracemalloc.Snapshot) -> AsyncSnapshot:
        return cls(snap.traces._traces, snap.traceback_limit)


class MemMonitor(commands.Cog):
    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.monitor_task = None

    async def display_top(
        self, snapshot: AsyncSnapshot, key_type: str = "lineno", limit: int = 15
    ) -> None:
        try:
            global _SEND_MESSAGE
            snapshot = await snapshot.filter_traces(
                (
                    tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
                    tracemalloc.Filter(False, "<unknown>"),
                )
            )
            top_stats = await snapshot.statistics(key_type)

            header = "=========================== Memory Breakdown ===========================\n"
            lines = f"Top {limit} lines\n"
            _SEND_MESSAGE = header
            _SEND_MESSAGE += lines
            for index, stat in enumerate(top_stats[:limit], 1):
                frame = stat.traceback[0]
                filename = os.sep.join(frame.filename.split(os.sep)[-2:])
                line_string = f"#{index}: {filename}:{frame.lineno}: {stat.size / 1024:.1f} KiB\n"
                _SEND_MESSAGE += line_string
                line = linecache.getline(frame.filename, frame.lineno).strip()
                if line:
                    extra_line = f"    {line}\n"
                    _SEND_MESSAGE += extra_line

            other = top_stats[limit:]
            if other:
                size = sum(stat.size for stat in other)
                mem_usage = f"{len(other)} other: {size / 1024:.1f} KiB\n"
                _SEND_MESSAGE += mem_usage
            total = sum(stat.size for stat in top_stats)
            total_mem_usage = f"Total allocated size: {total / 1024:.1f} KiB\n"
            _SEND_MESSAGE += total_mem_usage
        except Exception as exc:
            log.exception("error", exc_info=exc)
            raise

    async def memory_monitor(self, limit: int = 15) -> None:
        snapshot = None
        while True:
            if snapshot is None:
                with concurrent.futures.ProcessPoolExecutor() as executor:
                    snapshot = await self.bot.loop.run_in_executor(
                        executor, tracemalloc.take_snapshot
                    )
                    snapshot = AsyncSnapshot.from_sync(snapshot)
            if snapshot is not None:
                await self.display_top(snapshot, limit=limit)
                return

    def cog_unload(self) -> None:
        if self.monitor_task is not None:
            self.monitor_task.cancel()

    @commands.is_owner()
    @commands.group(name="memmon")
    async def memmon(self, ctx: commands.Context):
        """Options."""

    @commands.max_concurrency(1, per=commands.BucketType.user)
    @memmon.command(name="get")
    async def memmon_get(self, ctx: commands.Context, top: int = 15):
        """Get a trace of memory usage."""
        global _SEND_MESSAGE
        await ctx.tick()
        if self.monitor_task is not None:
            self.monitor_task.cancel()
        self.monitor_task = asyncio.create_task(self.memory_monitor(limit=top))
        await ctx.send("This may take a while, I'll ping you when it is done.")
        while not self.monitor_task.done():
            await asyncio.sleep(1)
        await ctx.send(f"{ctx.author.mention}, here is your memory snapshot.")
        if _SEND_MESSAGE:
            await ctx.send_interactive(pagify(_SEND_MESSAGE, page_length=1900), box_lang="py")
        _SEND_MESSAGE = ""
        with contextlib.suppress(Exception):
            self.monitor_task.cancel()
        self.monitor_task = None
