from typing import Sequence

import asyncio


class NameGenerator:
    """Yield entry every `delay` seconds."""

    def __init__(self, contents: Sequence, delay: float = 0.0):
        self.delay = delay
        self.content = contents
        self.i = 0
        self.to = len(contents)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.i >= self.to:
            raise StopAsyncIteration
        i = self.content[self.i]
        self.i += 1
        if self.i:
            await asyncio.sleep(self.delay)
        return i

