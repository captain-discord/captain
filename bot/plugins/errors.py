# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Any


# --------------------
# Builtin dependencies
# --------------------
from traceback import format_tb

# ------------------------
# Third-party dependencies
# ------------------------
from discord.ext import commands

# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint
from util import console
from util.constants import config
from util.exceptions import ArtemisException, UserNotFound


class Listeners(blueprint, commands.Cog, name="Error Listeners"):
    """This listens to discord.py for any exceptions triggered from running commands or events.
    
    If it was an event that failed, only the developers are notified. If it was a command failure, then the user is notified."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    @commands.Cog.listener() 
    async def on_command_error(self,
                               ctx: commands.Context,
                               error: Any):
        """This listener handles any unknown or generic errors that occur in commands.
        
        To determine whether an unknown error has occured, this listener checks the type of the error raised."""

        IGNORED = (commands.CheckFailure,
                   commands.CommandNotFound,
                   commands.NoPrivateMessage)

        if isinstance(error, IGNORED):
            return

        # =============================
        # Missing an argument somewhere
        # =============================
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(content=f"🚫 You're missing a required argument: `{error.param.name}`\n**Usage:** `{config.prefix.default}{ctx.command.usage}`")

        # ==========================
        # Improper argument provided
        # ========================== 
        if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # cheers to the d.py server for this line of code
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            argument = list(ctx.command.clean_params)[len(ctx.args[2:] if ctx.command.cog else ctx.args[1:])]

            return await ctx.send(content=f"🚫 You provided an imporper argument: `{argument}`\n**Usage:** `{config.prefix.default}{ctx.command.usage}`")

        if isinstance(error, commands.CommandInvokeError):
            # ========================
            # Custom exception handler
            # ========================
            if isinstance(error.original, ArtemisException):
                return self.artemis.dispatch(event_name="custom_error",
                                             ctx=ctx,
                                             error=error.original)

        await ctx.send(content="🚫 Unknown error, check the logs.")
        traceback = "\n".join(format_tb(tb=error.original.__traceback__))
        console.warn(text=f"Untracked error occured in {ctx.command}:\n\n{traceback}\n\n{error}")

    @commands.Cog.listener()
    async def on_custom_error(self,
                              ctx: commands.Context,
                              error: Any):
        """This specifically handles errors raised intentionally by artemis."""

        if isinstance(error, UserNotFound):
            return await ctx.send(content=f"🚫 Couldn't find the user your searched for.")

    @commands.Cog.listener()
    async def on_error(self,
                       event: str,
                       error: Any):
        """This handles logging for errors occuring in event listeners."""

        console.error(text=f"Error occured in {event}:\n\n{error}")

                        
LOCAL_COGS = [
    Listeners
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")