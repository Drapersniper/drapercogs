```py
bot.remove_cog("ErrorCounter")
# Standard Library
import sys

from collections import Counter, defaultdict

# Cog Dependencies
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands import Context


class DefaultDictCounter(defaultdict): # Modified defaultdict to add a `to_dict()` method to it
    def to_dict(self):
        return {k: dict(v) for k,v in self.items()}


class ErrorCounter(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot
        if not hasattr(bot, "_error_counter"): # Only inject this if this property doesnt exist
            self.bot._error_counter = DefaultDictCounter(Counter) # Use the modified `DefaultDictCounter` here instead of standard `defaultdict`

    @commands.Cog.listener()
    async def on_command_error(self, ctx: Context, error: BaseException): # Listen for command error
        if ctx:
            if getattr(ctx, "command", None):
                self.bot._error_counter[ctx.command.qualified_name][type(error).__qualname__] += 1 # Makes a counter of {Command : {ErrorT: number_of_ErrorT_seen}}
            else:
                self.bot._error_counter["No command"][type(error).__qualname__] += 1
        else:
            self.bot._error_counter["No Context"][type(error).__qualname__] += 1

    @commands.Cog.listener()
    async def on_error(self, event, *args, **kwargs): # Listen for errors in events
        error, value, traceback = sys.exc_info()
        self.bot._error_counter[f"event_{event}"][error.__qualname__] += 1
bot.add_cog(ErrorCounter(bot))
```
