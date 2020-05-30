# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis


# ------------------------
# Third-party dependencies
# ------------------------
import discord

from discord.ext import commands

# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint
from evaluator import register

from util import console
from util.constants import actions, cache, config, const, emojis, guilds


class Commands(blueprint, commands.Cog, name="Owner Commands", command_attrs=dict(hidden=True)):
    """These commands are very dangerous and should only be used by highly trusted actors.
    
    Basic functionality includes evaluation and shutdown amongst other utilities."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

        register(bot=artemis,
                 config={
                     "extra_attrs": dict(hidden=True),
                     "imports": [
                         "util",
                         "menus",
                         "custos"
                     ],
                     "vars": {
                         "actions": actions,
                         "cache": cache,
                         "config": config,
                         "console": console,
                         "const": const,
                         "emojis": emojis,
                         "guilds": guilds
                     }
                 })

    def cog_check(self,
                  ctx: commands.Context):
        """Ensures that only the bot owners can run these commands."""

        return self.artemis.is_owner(user=ctx.author)

    @commands.command(name="shutdown",
                      usage="shutdown",
                      aliases=["kill"])
    async def shutdown(self,
                       ctx: commands.Context):
        """Gracefully shuts the bot down."""

        await ctx.send(content=f"😴 Shutting down...")
        self.artemis.shutdown()


class Exceptions(blueprint, commands.Cog, name="Owner Exceptions"):
    """This is a collection of exceptions raised only in this file.
    
    This cog also comes equipped with its own command error listener."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    
LOCAL_COGS = [
    Commands
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")