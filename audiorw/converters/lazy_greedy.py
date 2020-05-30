# -*- coding: utf-8 -*-
# Cog Dependencies
from redbot.core import commands


class LazyGreedyConverter(commands.Converter):
    def __init__(self, splitter: str) -> None:
        self.splitter_Value = splitter

    async def convert(self, ctx: commands.Context, argument: str) -> str:
        full_message = ctx.message.content.partition(f" {argument} ")
        if len(full_message) == 1:
            full_message = (
                (argument if argument not in full_message else "") + " " + full_message[0]
            )
        elif len(full_message) > 1:
            full_message = (
                (argument if argument not in full_message else "") + " " + full_message[-1]
            )
        greedy_output = (" " + full_message.replace("—", "--")).partition(
            f" {self.splitter_Value}"
        )[0]
        return f"{greedy_output}".strip()
