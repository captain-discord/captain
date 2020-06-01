# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Any, List, Optional, Union


# --------------------
# Builtin dependencies
# --------------------
from datetime import datetime

# ------------------------
# Third-party dependencies
# ------------------------
import discord

from aiohttp import ClientSession
from discord.ext import commands

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from custos import blueprint

from util import console
from util.constants import config, emojis
from util.exceptions import ArtemisException, UserNotFound


async def upload_archive(author_id: int,
                         guild_id: int,
                         messages: List[discord.Message]) -> str:
    """Uploads an archive to the archive API and returns the URL.
    
    If the server returns an errored response, an exception is raised."""

    payload = {
        "author_id": author_id,
        "guild_id": guild_id,
        "messages": []
    }

    for message in messages:
        payload["messages"].append({
            "content": message.content,
            "attachment": message.attachments[0].url if message.attachments else "",
            "embed": message.embeds[0].to_dict() if message.embeds else None,
            
            "message": message.id,
            "channel": message.channel.id,
            "author": message.author.id,
            "username": str(message.author),

            "timestamp": message.created_at.strftime("%Y-%m-%d %H:%M:%S.%f")
        })

    async with ClientSession() as session:
        async with session.post(url=config.website + config.archive.endpoint,
                                headers={
                                    "Authorization": config.archive.token
                                },
                                json=payload) as res:
            if 200 <= res.status < 300:
                key = await res.json()
                return f"{config.website}{config.archive.endpoint}/{key['key']}?view=webpage"

            else:
                raise Exceptions.ArchiveFailed(code=res.status)


class Commands(blueprint, commands.Cog, name="Archive Commands"):
    """Archiving messages allows server Staff to save logs of messages from bad actors and co."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    @commands.group(name="archive",
                    usage="archive <subcommand:text>",
                    invoke_without_command=True)
    async def archive(self,
                      ctx: commands.Context):
        """Saves a list of messages to a special API for use later."""

        await ctx.send(content=f"🚫 You're missing a subcommand, use **{config.prefix.default}help archive** for help.")

    @archive.command(name="here",
                     usage="archive here <amount:num>")
    async def archive_here(self,  
                           ctx: commands.Context,
                           amount: int):
        """Archives an amount of messages in the current channel."""

        messages = await ctx.channel.history(limit=amount).flatten()
        messages.reverse()

        url = await upload_archive(author_id=ctx.author.id,
                                   guild_id=ctx.guild.id,
                                   messages=messages)

        await ctx.send(content=f"{emojis.tick_yes} {len(messages)} messages have been archived at:\n{url}")

    @archive.command(name="user",
                     usage="archive user <amount:num> <target:user>")
    async def archive_user(self,  
                           ctx: commands.Context,
                           amount: int,
                           target: Union[discord.Member, discord.User, int]):
        """Archives an amount of messages in the current channel that were sent by a user."""

        if not isinstance(target, (discord.Member, discord.User)):
            target_id = utils.intable(obj=target)
            target = await self.artemis.fetch_user(user_id=target_id)

            if not target_id or target is None:
                raise UserNotFound(query=target)

        messages = await ctx.channel.history(limit=amount,
                                             check=lambda m: m.author == target).flatten()
        messages.reverse()

        url = await upload_archive(author_id=ctx.author.id,
                                   guild_id=ctx.guild.id,
                                   messages=messages)

        await ctx.send(content=f"{emojis.tick_yes} {len(messages)} messages have been archived at:\n{url}")

    @archive.command(name="channel",
                     usage="archive channel <amount:num> <target:channel>")
    async def archive_channel(self,  
                              ctx: commands.Context,
                              amount: int,
                              target: discord.TextChannel):
        """Archives an amount of messages in the specified channel."""

        messages = await target.history(limit=amount).flatten()
        messages.reverse()

        url = await upload_archive(author_id=ctx.author.id,
                                   guild_id=ctx.guild.id,
                                   messages=messages)

        await ctx.send(content=f"{emojis.tick_yes} {len(messages)} messages have been archived at:\n{url}")

    @archive.command(name="bots",
                     usage="archive bots <amount:num> [target:channel]")
    async def archive_bots(self,  
                           ctx: commands.Context,
                           amount: int,
                           target: Optional[discord.TextChannel] = None):
        """Archives an amount of messages sent by bots in the current or specified channel."""

        target = target or ctx.channel

        messages = await target.history(limit=amount,
                                        check=lambda m: m.author.bot).flatten()
        messages.reverse()

        url = await upload_archive(author_id=ctx.author.id,
                                   guild_id=ctx.guild.id,
                                   messages=messages)

        await ctx.send(content=f"{emojis.tick_yes} {len(messages)} messages have been archived at:\n{url}")


class Exceptions(blueprint, commands.Cog, name="Archive Exceptions"):
    """This is a collection of exceptions raised only in this file.
    
    This cog also comes equipped with its own command error listener."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    
    class ArchiveFailed(ArtemisException):
        def __init__(self,
                     code: int):
            self.code = code

            console.error(text=f"Failed to upload to archive API with code {code}.")

    
    @commands.Cog.listener()
    async def on_command_error(self,
                               ctx: commands.Context,
                               error: Any):
        """This handles the error responses for when exceptions listed in this cog are raised."""
    
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, self.ArchiveFailed):
                return await ctx.send(content=f"🚫 Failed to contact archiving server. Check the logs.")


LOCAL_COGS = [
    Commands,
    Exceptions
]


def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")