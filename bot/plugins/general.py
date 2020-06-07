# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Any, Optional


# --------------------
# Builtin dependencies
# --------------------
import os.path

from inspect import getsourcelines
from time import perf_counter

# ------------------------
# Third-party dependencies
# ------------------------
import discord

from discord.ext import commands

# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint
from util import console
from util.constants import emojis
from util.exceptions import ArtemisException


class Commands(blueprint, commands.Cog, name="General Commands"):
    """Below are your fairly average commands that don't really fit into any other category.
    
    These commands tend to be ping and the like."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    @commands.command(name="invite",
                      usage="invite [bot:user] [flags:text]")
    async def invite(self,
                     ctx: commands.Context,
                     bot: Optional[discord.User] = None,
                     *, flags: Optional[str] = ""):
        """Retrieves the invite URL pertaining to a particular bot.
        
        If no bot is provided, then the invite for the current client is returned."""

        message = await ctx.send(content="⌛ Generating an invite...")

        BASE = "https://discord.com/api/oauth2/authorize?client_id={id}&permissions={perms}&scope=bot"
        PERM_FLAGS = {
            "-a": 8,
            "--administrator": 8,

            "-val": 128,
            "--view-audit-log": 128,

            "-ms": 32,
            "--manage-server": 32,

            "-mr": 268435456,
            "--manage-roles": 268435456,

            "-mc": 16,
            "--manage-channels": 16,

            "-km": 2,
            "--kick-members": 2,

            "-bm": 4,
            "--ban-members": 4,

            "-cii": 1,
            "--create-instant-invite": 1,

            "-cn": 67108864,
            "--change-nickname": 67108864,

            "-mn": 134217728,
            "--manage-nicknames": 134217728,

            "-me": 1073741824,
            "--manage-emojis": 1073741824,

            "-mw": 536870912,
            "--manage-webhooks": 536870912,

            "-rm": 1024,
            "--read-messages": 1024,

            "-sm": 2048,
            "--send-messages": 2048,

            "-stm": 4096,
            "--send-tts-messages": 4096,

            "-mm": 8192,
            "--manage-messages": 8192,

            "-el": 16384,
            "--embed-links": 16384,

            "-af": 32768,
            "--attach-files": 32768,

            "-rmh": 65536,
            "--read-message-history": 65536,

            "-mar": 131072,
            "--mention-all-roles": 131072,

            "-uee": 262144,
            "--use-external-emojis": 262144,

            "-ar": 64,
            "--add-reactions": 64,

            "-c": 1048576,
            "--connect": 1048576,

            "-mu": 4194304,
            "--mute-members": 4194304,

            "-mv": 16777216,
            "--move-members": 16777216,

            "-s": 2097152,
            "--speak": 2097152,

            "-dm": 8388608,
            "--deafen-members": 8388608,

            "-uva": 33554432,
            "--use-voice-activity": 33554432,

            "-ps": 256,
            "--priority-speaker": 256
        }

        bot = bot or self.artemis.user

        if not bot.bot:
            raise Exceptions.NotABot(user=bot)

        permissions = []
        for flag in flags.split(" "):
            if flag in PERM_FLAGS.keys():
                perm_id = PERM_FLAGS[flag]

                if perm_id not in permissions:
                    permissions.append(perm_id)

        await message.edit(content=f"{emojis.tick_yes} Generated an invite for {bot}{f' with {len(permissions)} permission flags' if len(permissions) > 0 else ''}:\n<{BASE.format(id=bot.id, perms=sum(permissions))}>")

    @commands.command(name="ping",
                      usage="ping",
                      aliases=["heartbeat", "latency"])
    async def ping(self,
                   ctx: commands.Context):
        """Shows information about the speed of the bot's connection to Discord."""

        start = perf_counter()
        message = await ctx.send(content="⏱️ Pinging connection latency...")
        stop = perf_counter()

        msg_latency = round((stop - start) * 1000)

        await message.edit(content=f"🏓 **Roundtrip:** {msg_latency} ms | **Websocket:** {round(ctx.bot.latency * 1000)} ms")

    @commands.command(name="source",
                      usage="source [command:text]")
    async def source(self,
                     ctx: commands.Context,
                     *, command: Optional[str] = None):
        """Gets the GitHub repo URL for the full bot or specific command.
        
        For subcommands, separate it using periods or spaces. E.g: inf search/inf.search."""

        BASE = "https://github.com/Jack-Gledhill/artemis"
        BRANCH = "master"

        if command is None:
            return await ctx.send(content=f"🔧 Source for full bot:\n<{BASE}>")

        cmd_obj = self.artemis.get_command(name=command.replace(".", " "))
        
        if cmd_obj is None:
            raise Exceptions.LookupFailed(query=command)
        
        src = cmd_obj.callback.__code__
        lines, firstlineno = getsourcelines(object=src)
        location = os.path.relpath(path=src.co_filename).replace("\\", "/")

        await ctx.send(content=f"🔧 Source for {cmd_obj.name} command:\n<{BASE}/blob/{BRANCH}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>")


class Exceptions(blueprint, commands.Cog, name="General Exceptions"):
    """This is a collection of exceptions raised only in this file.
    
    This cog also comes equipped with its own command error listener."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    
    class LookupFailed(ArtemisException):
        def __init__(self,
                     query: str):
            self.query = query


    class InviteException(ArtemisException):
        pass


    class NotABot(InviteException):
        def __init__(self,
                    user: discord.User):
            self.user = user


    @commands.Cog.listener()
    async def on_command_error(self,
                               ctx: commands.Context,
                               error: Any):
        """This handles the error responses for when exceptions listed in this cog are raised."""
    
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, self.LookupFailed):
                return await ctx.send(content=f"🚫 Couldn't find any commands matching `{error.original.query}`.")


LOCAL_COGS = [
    Commands,
    Exceptions
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")