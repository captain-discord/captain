# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Any, Union


# --------------------
# Builtin dependencies
# --------------------
from datetime import datetime

# ------------------------
# Third-party dependencies
# ------------------------
import discord

from discord.ext import commands

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from custos import blueprint

from util import console
from util.constants import actions, guilds


class Listeners(blueprint, commands.Cog, name="Logging Listeners"):
    """These listeners add functionality to logging and use the resources in actions.yml."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    @commands.Cog.listener()
    async def on_message_edit(self,
                              before: discord.Message,
                              after: discord.Message):
        """Handles logging for edited messages."""

        if not guilds.get(after.guild.id, {}) or after.content == before.content:
            return
        
        self.artemis.dispatch(event_name="logging_action",
                              guild=after.guild,
                              action="MESSAGE_EDIT",
                              
                              before=before,
                              after=after)

    @commands.Cog.listener()
    async def on_message_delete(self,
                                message: discord.Message):
        """Handles logging for deleted messages."""

        if not guilds.get(message.guild.id, {}) or not message.content:
            return
        
        self.artemis.dispatch(event_name="logging_action",
                              guild=message.guild,
                              action="MESSAGE_DELETE",
                              
                              message=message)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self,
                                         payload: discord.RawBulkMessageDeleteEvent):
        """Handles logging for purged messages."""

        channel = self.artemis.get_channel(id=payload.channel_id)       

        if not guilds.get(channel.guild.id, {}):
            return
        
        self.artemis.dispatch(event_name="logging_action",
                              guild=channel.guild,
                              action="MESSAGE_BULK_DELETE",
                              
                              amount=len(payload.message_ids),
                              channel=channel)
        
    @commands.Cog.listener()
    async def on_member_join(self,
                             member: discord.Member):
        """Handles logging for new members."""

        if not guilds.get(member.guild.id, {}):
            return
        
        self.artemis.dispatch(event_name="logging_action",
                              guild=member.guild,
                              action="MEMBER_JOIN",
                              
                              user=member,
                              ordinal=utils.ordinal_indicator(num=member.guild.member_count + 1))

    @commands.Cog.listener()
    async def on_member_remove(self,
                               member: discord.Member):
        """Handles logging for members that have left."""

        if not guilds.get(member.guild.id, {}):
            return
        
        self.artemis.dispatch(event_name="logging_action",
                              guild=member.guild,
                              action="MEMBER_LEAVE",
                              
                              user=member,
                              joined_ago=utils.time_since(since=member.joined_at,
                                                          ms=False,
                                                          granularity=2,
                                                          pretty=True,
                                                          skip_empty=True))

    @commands.Cog.listener(name="on_guild_channel_delete")
    @commands.Cog.listener(name="on_guild_role_delete")
    async def channel_or_role_delete(self,
                                     channel_or_role: Union[discord.abc.GuildChannel, discord.Role]):
        """Handles logging of channel/role deletion.
        
        If this triggers for a channel, the event takes into account the type of the channel (text/voice/category) and notes it in the log."""

        if not guilds.get(channel_or_role.guild.id, {}):
            return

        if isinstance(channel_or_role, discord.Role):
            action = "ROLE_DELETE"
            kwargs = {"role": channel_or_role}

        else:
            action = "CHANNEL_DELETE"
            kwargs = {"channel": channel_or_role}

        self.artemis.dispatch(event_name="logging_action",
                              guild=channel_or_role.guild,
                              action=action,
                              
                              **kwargs)

    @commands.Cog.listener(name="on_guild_channel_create")
    @commands.Cog.listener(name="on_guild_role_create")
    async def channel_or_role_create(self,
                                     channel_or_role: Union[discord.abc.GuildChannel, discord.Role]):
        """Handles logging of channel/role creation.
        
        If this triggers for a channel, the event takes into account the type of the channel (text/voice/category) and notes it in the log."""

        if not guilds.get(channel_or_role.guild.id, {}):
            return

        if isinstance(channel_or_role, discord.Role):
            action = "ROLE_CREATE"
            kwargs = {"role": channel_or_role}

        else:
            action = "CHANNEL_CREATE"
            kwargs = {"channel": channel_or_role}

        self.artemis.dispatch(event_name="logging_action",
                              guild=channel_or_role.guild,
                              action=action,
                              
                              **kwargs)

    @commands.Cog.listener()
    async def on_member_update(self,
                               before: discord.Member,
                               after: discord.Member):
        """This handles nickname logging."""

        if before.nick == after.nick or not guilds.get(after.guild.id, {}):
            return

        # ================
        # Nickname removed
        # ================
        if after.nick is None:
            action = "NICKNAME_REMOVE"
            kwargs = {
                "user": after,
                "nick": before.nick
            }

        # ==============
        # Nickname added
        # ==============
        elif before.nick is None:
            action = "NICKNAME_ADD"
            kwargs = {
                "user": after,
                "nick": after.nick
            }

        else:
            action = "NICKNAME_CHANGE"
            kwargs = {
                "user": after,
                "before": before.nick,
                "after": after.nick
            }

        self.artemis.dispatch(event_name="logging_action",
                              guild=after.guild,
                              action=action,
                              
                              **kwargs)

    @commands.Cog.listener()
    async def on_logging_action(self,
                                guild: discord.Guild,
                                action: str,
                                **log_data: dict):
        """Triggered every time a new logging event is dispatched.
        
        All of the formatting data is found in the log_data kwargs."""

        action = action.upper()
        fmt = actions.get(action)

        if fmt is None:
            return console.warn(text=f"An unknown logging event ({action}) was dispatched to {guild.id}.")

        channel_ids = utils.all(iterable=guilds.get(guild.id, {}).get("channels", {}).items(),
                                condition=lambda c: action in c[1])

        if not channel_ids:
            return

        channels = {self.artemis.get_channel(id=channel_id[0]) for channel_id in channel_ids}

        for channel in channels:
            if channel is None:
                continue

            if not channel.permissions_for(member=guild.me).send_messages:
                continue

            await channel.send(content=actions.base.format(at=datetime.utcnow().strftime(actions.time_format),
                                                           emoji=fmt.get("emoji", "❔"),
                                                           text=fmt.get("text", "").format(**log_data)))

        console.debug(text=f"Successfully dispatched {action} event to {guild.id}.")


LOCAL_COGS = [
    Listeners
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")