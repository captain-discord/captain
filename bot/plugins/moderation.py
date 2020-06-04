# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Any, Optional, Union


# --------------------
# Builtin dependencies
# --------------------
from datetime import datetime, timedelta
from re import compile, findall, finditer, IGNORECASE, search

# ------------------------
# Third-party dependencies
# ------------------------
import discord

from discord.ext import commands
from tabulate import tabulate

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from custos import blueprint

from plugins.timers import Timer

from util import console
from util.constants import config, emojis, guilds, postgres, redis
from util.enumerators import InfractionType
from util.exceptions import ArtemisException, UserNotFound


async def new_infraction(artemis: Artemis,
                         **inf_data: dict):
    """Handles logging and insertion of infraction data into the database."""

    guild = inf_data.pop("guild")
    type_id = inf_data.pop("type", "BAN")
    reason = inf_data.pop("reason", "N/A")
    target = inf_data.pop("target")
    actor = inf_data.pop("actor")
    dur_friendly = inf_data.pop("dur_friendly", None)

    async with postgres.acquire() as con:
        query_1 = """SELECT case_id 
                     FROM infractions
                     WHERE guild_id = $1
                     ORDER BY case_id DESC
                     LIMIT 1;"""

        last_case_id = await con.fetchval(query_1,
                                          guild.id)

        last_case_id = last_case_id or 0

        query_2 = """INSERT INTO infractions (case_id, guild_id, actor_id, target_id, type_id, reason, timestamp)
                     VALUES ($1, $2, $3, $4, $5, $6, $7);"""

        await con.execute(query_2,
                          last_case_id + 1, guild.id, actor.id, target.id, getattr(InfractionType, type_id, -1), reason, datetime.utcnow())

    if dur_friendly:
        artemis.dispatch(event_name="logging_action",
                         guild=guild,
                         action="MEMBER_" + type_id,
                            
                         actor=actor,
                         user=target,
                         reason=reason,
                         case=last_case_id + 1,
                         duration=dur_friendly)

        return last_case_id + 1

    artemis.dispatch(event_name="logging_action",
                     guild=guild,
                     action="MEMBER_" + type_id,
                            
                     actor=actor,
                     user=target,
                     reason=reason,
                     case=last_case_id + 1)

    return last_case_id + 1


class Commands(blueprint, commands.Cog, name="Moderation Commands"):
    """These commands allow server Moderators and Administrators to deal with rule breakers in the server."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    class DurationConverter(commands.Converter):
        """This handles conversion of a human duration into something the bot can understand properly.
        
        This is great for temp mutes/bans and lockdowns."""

        TIME_DICT = {
            "s": 1, 
            "sec": 1,
            "secs": 1,
            "second": 1,
            "seconds": 1,
            
            "m": 60, 
            "min": 60,
            "mins": 60,
            "minute": 60,
            "minutes": 60,    
            
            "h": 3600, 
            "hr": 3600, 
            "hrs": 3600, 
            "hour": 3600,
            "hours": 3600,
            
            "d": 86400,
            "day": 86400,
            "days": 86400,

            "w": 604800,
            "wk": 604800,
            "wks": 604800,
            "week": 604800,
            "weeks": 604800,

            "mth": 86400 * 30,
            "mths": 86400 * 30,
            "month": 86400 * 30,
            "months": 86400 * 30,

            "y": 86400 * 365,
            "yr": 86400 * 365,
            "yrs": 86400 * 365,
            "year": 86400 * 365,
            "years": 86400 * 365
        }
        TIME_REGEX = compile(rf"(?:([0-9]+)\s?({'|'.join(key for key in TIME_DICT.keys())}))+?")

        async def convert(self, 
                          argument: str):
            time = 0
            
            for v, k in findall(self.TIME_REGEX, argument.lower()):
                try:
                    time += self.TIME_DICT[k] * float(v)
            
                except (KeyError, ValueError):
                    raise Exceptions.ImproperDuration()
            
            return time

    def cog_check(self,
                  ctx: commands.Context):
        if ctx.author.guild_permissions.administrator:
            return True

        return False

    def can_punish(self,
                   actor: discord.Member,
                   target: Union[discord.Member, discord.User]):
        """This checks if the target can be punished by the actor.
        
        If the check fails then the appropriate error is raised, cancelling the command."""

        # ===========================================================
        # None of the checks here apply to users outside of the guild
        # ===========================================================
        if isinstance(target, discord.User):
            return

        # =========================
        # You can't punish yourself
        # =========================
        if actor == target:
            raise Exceptions.CannotPunishUser(user=target,
                                              reason="Punishing yourself wouldn't be the smartest idea now, would it?")

        # ============================================
        # We definitely can't punsih the guild's owner
        # ============================================
        if target == actor.guild.owner:
            raise Exceptions.CannotPunishUser(user=target,
                                              reason=f"{target} is the owner of the server, I can't punish them.")

        #===================================
        # This one is a role hierarchy check
        # ==================================
        if target.top_role >= actor.top_role and actor != actor.guild.owner:
            raise Exceptions.CannotPunishUser(user=target,
                                              reason=f"Your highest role ({actor.top_role.mention}) must be above {target}'s highest role ({target.top_role.mention})")

        # ================================================================
        # This one checks if the bot is even capable of punishing the user
        # ================================================================
        if target.top_role >= actor.guild.me.top_role:
            raise Exceptions.CannotPunishUser(user=target,
                                              reason=f"My highest role ({actor.guild.me.top_role.mention}) needs to be above {target}'s highest role ({target.top_role.mention})")

    @commands.command(name="bean",
                      usage="bean <target:user> [reason:text]",
                      hidden=True)
    @commands.bot_has_permissions(ban_members=True)
    async def bean(self,
                   ctx: commands.Context,
                   target: discord.Member,
                   *, reason: Optional[str] = "No reason given."):
        """Beans a member from the server."""

        self.can_punish(actor=ctx.author,
                        target=target)

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been beaned for:\n{reason}")

    @commands.command(name="ban",
                      usage="ban <target:user> [reason:text]")
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self,
                  ctx: commands.Context,
                  target: Union[discord.Member, discord.User, int],
                  *, reason: Optional[str] = "No reason given."):
        """Bans a member from the server.
        
        If the target is an ID of an otherwise unknown user, the bot attempts to perform a hack ban."""

        if not isinstance(target, (discord.Member, discord.User)):
            target_id = utils.intable(obj=target)
            target = await self.artemis.fetch_user(user_id=target_id)

            if not target_id or target is None:
                raise UserNotFound(query=target)

        try:
            past_ban = await ctx.guild.fetch_ban(user=target)

            if past_ban:
                raise Exceptions.AlreadyBanned(user=target,
                                               reason=past_ban[1])

        except discord.NotFound:
            self.can_punish(actor=ctx.author,
                            target=target)

            await ctx.guild.ban(user=target,
                                reason=f"{ctx.author}: {reason}")

            await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been banned for:\n{reason}")        

            await new_infraction(artemis=self.artemis,
                                 guild=ctx.guild,
                                 actor=ctx.author,
                                 target=target,
                                 reason=reason,
                                 type=ctx.command.name.upper())

    @commands.command(name="softban",
                      usage="softban <target:user> [reason:text]",
                      aliases=["sban"])
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self,
                      ctx: commands.Context,
                      target: Union[discord.Member, discord.User, int],
                      *, reason: Optional[str] = "No reason given."):
        """Soft bans a member from the server.
        
        If the target is an ID of an otherwise unknown user, the bot attempts to perform a hack soft ban."""

        if not isinstance(target, (discord.Member, discord.User)):
            target_id = utils.intable(obj=target)
            target = await self.artemis.fetch_user(user_id=target_id)

            if not target_id or target is None:
                raise UserNotFound(query=target)

        try:
            past_ban = await ctx.guild.fetch_ban(user=target)

            if past_ban:
                raise Exceptions.AlreadyBanned(user=target,
                                               reason=past_ban[1])

        except discord.NotFound:
            self.can_punish(actor=ctx.author,
                            target=target)

            await ctx.guild.ban(user=target,
                                reason=f"{ctx.author}: {reason}")

            await ctx.guild.unban(user=target)

            await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been soft banned for:\n{reason}")

            await new_infraction(artemis=self.artemis,
                                 guild=ctx.guild,
                                 actor=ctx.author,
                                 target=target,
                                 reason=reason,
                                 type=ctx.command.name.upper())

    @commands.command(name="tempban",
                      usage="tempban <target:user> <duration:text> [reason:text]")
    @commands.bot_has_permissions(ban_members=True)
    async def tempban(self,
                      ctx: commands.Context,
                      target: Union[discord.Member, discord.User, int],
                      duration: str,
                      *, reason: Optional[str] = "No reason given."):
        """Bans a member of the server for a certain amount of time."""

        if not isinstance(target, (discord.Member, discord.User)):
            target_id = utils.intable(obj=target)
            target = await self.artemis.fetch_user(user_id=target_id)

            if not target_id or target is None:
                raise UserNotFound(query=target)

        try:
            past_ban = await ctx.guild.fetch_ban(user=target)

            if past_ban:
                raise Exceptions.AlreadyBanned(user=target,
                                               reason=past_ban[1])

        except discord.NotFound:
            self.can_punish(actor=ctx.author,
                            target=target)

            await ctx.guild.ban(user=target,
                                reason=f"{ctx.author}: {reason}")

            time_to_wait = await self.DurationConverter().convert(argument=duration)

            if time_to_wait == 0:
                raise Exceptions.DurationRequired()
                
            friendly_string = utils.time_since(seconds=time_to_wait,
                                               pretty=True,
                                               ms=False,
                                               granularity=7,
                                               skip_empty=True)

            case = await new_infraction(artemis=self.artemis,
                                        guild=ctx.guild,
                                        actor=ctx.author,
                                        target=target,
                                        reason=reason,
                                        type=ctx.command.name.upper(),
                                        dur_friendly=friendly_string)

            await self.artemis.timer_backend.create_new_timer(artemis=self.artemis,
                                                              event="temp_ban",
                                                              expire_at=datetime.utcnow() + timedelta(seconds=time_to_wait),
                                                              extras={
                                                                  "target": target.id,
                                                                  "guild": ctx.guild.id,
                                                                  "case": case
                                                              })

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been banned for {friendly_string} for:\n{reason}")

    @commands.command(name="unban",
                      usage="unban <target:user>")
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self,
                    ctx: commands.Context,
                    target: Union[discord.Member, discord.User, int]):
        """Unbans a member from the server.
        
        If the target is an ID of an otherwise unknown user, the bot attempts to perform a hack unban."""

        if not isinstance(target, (discord.Member, discord.User)):
            target_id = utils.intable(obj=target)
            target = await self.artemis.fetch_user(user_id=target_id)

            if not target_id or target is None:
                raise UserNotFound(query=target)

        try:
            past_ban = await ctx.guild.fetch_ban(user=target)

            await ctx.guild.unban(user=target,
                                  reason=str(ctx.author))

            await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been unbanned.")

            self.artemis.dispatch(event_name="logging_action",
                                  guild=ctx.guild,
                                  action="MEMBER_UNBAN",
                                
                                  actor=ctx.author,
                                  user=target)

        except discord.NotFound:
            raise Exceptions.BanNotFound(user=target)

    @commands.command(name="kick",
                      usage="kick <target:user> [reason:text]")
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self,
                   ctx: commands.Context,
                   target: discord.Member,
                   *, reason: Optional[str] = "No reason given."):
        """Kicks a member from the server.
        
        Obviously, the user has to be in the server for this command to work."""

        self.can_punish(actor=ctx.author,
                        target=target)

        await ctx.guild.kick(user=target,
                                reason=f"{ctx.author}: {reason}")

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been kicked for:\n{reason}")

        await new_infraction(artemis=self.artemis,
                             guild=ctx.guild,
                             actor=ctx.author,
                             target=target,
                             reason=reason,
                             type=ctx.command.name.upper())

    @commands.command(name="mute",
                      usage="mute <target:user> [reason:text]")
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self,
                   ctx: commands.Context,
                   target: discord.Member,
                   *, reason: Optional[str] = "No reason given."):
        """Adds the muted role to a member of the server."""

        self.can_punish(actor=ctx.author,
                        target=target)

        role = ctx.guild.get_role(role_id=guilds.get(ctx.guild.id, {}).get("moderation", {}).get("mute_role"))

        if role is None:
            raise Exceptions.MuteRoleNotConfigured()

        if role in target.roles:
            raise Exceptions.AlreadyMuted(user=target)

        await target.add_roles(role,
                               reason=f"{ctx.author}: {reason}")

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been muted for:\n{reason}")

        await new_infraction(artemis=self.artemis,
                             guild=ctx.guild,
                             actor=ctx.author,
                             target=target,
                             reason=reason,
                             type=ctx.command.name.upper())

    @commands.command(name="tempmute",
                      usage="tempmute <target:user> <duration:text> [reason:text]")
    @commands.bot_has_permissions(manage_roles=True)
    async def tempmute(self,
                       ctx: commands.Context,
                       target: discord.Member,
                       duration: str,
                       *, reason: Optional[str] = "No reason given."):
        """Adds the muted role to a member of the server for a certain amount of time."""

        self.can_punish(actor=ctx.author,
                        target=target)

        role = ctx.guild.get_role(role_id=guilds.get(ctx.guild.id, {}).get("moderation", {}).get("mute_role"))

        if role is None:
            raise Exceptions.MuteRoleNotConfigured()

        if role in target.roles:
            raise Exceptions.AlreadyMuted(user=target)

        await target.add_roles(role,
                               reason=f"{ctx.author}: {reason}")

        time_to_wait = await self.DurationConverter().convert(argument=duration)

        if time_to_wait == 0:
            raise Exceptions.DurationRequired()
            
        friendly_string = utils.time_since(seconds=time_to_wait,
                                           pretty=True,
                                           ms=False,
                                           granularity=7,
                                           skip_empty=True)

        case = await new_infraction(artemis=self.artemis,
                                    guild=ctx.guild,
                                    actor=ctx.author,
                                    target=target,
                                    reason=reason,
                                    type=ctx.command.name.upper(),
                                    dur_friendly=friendly_string)

        await self.artemis.timer_backend.create_new_timer(artemis=self.artemis,
                                                          event="temp_mute",
                                                          expire_at=datetime.utcnow() + timedelta(seconds=time_to_wait),
                                                          extras={
                                                              "target": target.id,
                                                              "guild": ctx.guild.id,
                                                              "case": case
                                                          })

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been muted for {friendly_string} for:\n{reason}")

    @commands.command(name="unmute",
                      usage="unmute <target:user>")
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self,
                     ctx: commands.Context,
                     target: discord.Member):
        """Removes the muted role from a member of the server."""

        self.can_punish(actor=ctx.author,
                        target=target)

        role = ctx.guild.get_role(role_id=guilds.get(ctx.guild.id, {}).get("moderation", {}).get("mute_role"))
        if role is None:
            raise Exceptions.MuteRoleNotConfigured()

        if role not in target.roles:
            raise Exceptions.NotMuted(user=target)

        await target.remove_roles(role,
                                  reason=str(ctx.author))

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been unmuted.")

        self.artemis.dispatch(event_name="logging_action",
                              guild=ctx.guild,
                              action="MEMBER_UNMUTE",
                                
                              actor=ctx.author,
                              user=target)

    @commands.command(name="warn",
                      usage="warn <target:user> <reason:text>")
    async def warn(self,
                   ctx: commands.Context,
                   target: discord.Member,
                   *, reason: str):
        """Gives a user a warning with a given reason."""

        self.can_punish(actor=ctx.author,
                        target=target)

        await ctx.send(content=f"{emojis.tick_yes} {target} (`{target.id}`) has been warned for:\n{reason}")

        await new_infraction(artemis=self.artemis,
                             guild=ctx.guild,
                             actor=ctx.author,
                             target=target,
                             reason=reason,
                             type=ctx.command.name.upper())

    @commands.group(name="purge",
                    usage="purge <subcommand:text>",
                    invoke_without_command=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self,
                    ctx: commands.Context):
        """Allows moderators to purge any number of messages sent in chat."""

        await ctx.send(content=f"🚫 You're missing a subcommand, use **{config.prefix.default}help purge** for help.")

    @purge.command(name="here",
                   usage="purge here <amount:num>")
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_here(self,  
                         ctx: commands.Context,
                         amount: int):
        """Purges an amount of messages in the current channel."""

        await ctx.message.delete()
        purged = await ctx.channel.purge(limit=amount)
        await ctx.send(content=f"{emojis.tick_yes} {len(purged)} messages have been purged.",
                       delete_after=15)

    @purge.command(name="user",
                   usage="purge user <amount:num> <target:user>")
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_user(self,  
                         ctx: commands.Context,
                         amount: int,
                         target: Union[discord.Member, discord.User, int]):
        """Purges an amount of messages in the current channel that were sent by a user."""

        await ctx.message.delete()

        if not isinstance(target, (discord.Member, discord.User)):
            target_id = utils.intable(obj=target)
            target = await self.artemis.fetch_user(user_id=target_id)

            if not target_id or target is None:
                raise UserNotFound(query=target)

        purged = await ctx.channel.purge(limit=amount,
                                         check=lambda m: m.author.id == target.id)
        await ctx.send(content=f"{emojis.tick_yes} {len(purged)} messages by {target} have been purged.",
                       delete_after=15)

    @purge.command(name="channel",
                   usage="purge channel <amount:num> <target:channel>")
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_channel(self,  
                            ctx: commands.Context,
                            amount: int,
                            target: discord.TextChannel):
        """Purges an amount of messages in the specified channel."""

        await ctx.message.delete()
        purged = await target.purge(limit=amount)
        await ctx.send(content=f"{emojis.tick_yes} {len(purged)} messages in {target.mention} have been purged.",
                       delete_after=15)

    @purge.command(name="bots",
                   usage="purge bots <amount:num> [target:channel]")
    @commands.bot_has_permissions(manage_messages=True)
    async def purge_bots(self,  
                         ctx: commands.Context,
                         amount: int,
                         target: Optional[discord.TextChannel] = None):
        """Purges an amount of messages sent by bots in the current or specified channel."""

        await ctx.message.delete()

        target = target or ctx.channel

        purged = await target.purge(limit=amount,
                                    check=lambda m: m.author.bot)
        await ctx.send(content=f"{emojis.tick_yes} {len(purged)} messages in {target.mention} by bot accounts have been purged.",
                       delete_after=15)

    @commands.group(name="inf",
                    usage="inf <subcommand:text>",
                    aliases=["infractions"],
                    invoke_without_command=True)
    async def inf(self,
                  ctx: commands.Context):
        """A useful utility that allows Moderators to manage server infractions."""

        await ctx.send(content=f"🚫 You're missing a subcommand, use **{config.prefix.default}help inf** for help.")

    @inf.command(name="clear",
                 usage="inf clear <target:user|num>")
    async def inf_clear(self,
                        ctx: commands.Context,
                        target: Union[discord.User, int]):
        """Removes either a single infraction or all infractions pertaining to a specified target.
        
        Unlike search, providing a user will not remove infractions where the user is the actor."""

        async with postgres.acquire() as con:
            if isinstance(target, discord.User):
                search_id = target.id
                query = """DELETE FROM infractions
                           WHERE target_id = $1
                           AND guild_id = $2

                           RETURNING *;"""

            else:
                search_id = target
                query = """DELETE FROM infractions
                           WHERE case_id = $1
                           AND guild_id = $2
                           
                           RETURNING *;"""

            cases = await con.fetch(query,
                                    search_id, ctx.guild.id)

            if not cases:
                raise Exceptions.InfractionsNotFound(query=target)

            await ctx.send(content=f"{emojis.tick_yes} {len(cases)} infractions have been cleared.")

    @inf.command(name="search",
                 usage="inf search <target:user|num>")
    async def inf_search(self,
                         ctx: commands.Context,
                         target: Union[discord.User, int]):
        """Searches for either a user's infractions or a specific infraction by it's ID."""

        MAX = 10
        TS_FORMAT = "%d/%m/%y %H:%M:%S"

        async with postgres.acquire() as con:
            if isinstance(target, (discord.ClientUser, discord.User)):
                search_id = target.id
                query = """SELECT case_id, target_id, actor_id, type_id, reason, timestamp
                           FROM infractions
                           WHERE (target_id = $1
                           OR actor_id = $1)
                           AND guild_id = $2
                           ORDER BY case_id DESC;"""

            else:
                search_id = target
                query = """SELECT case_id, target_id, actor_id, type_id, reason, timestamp
                           FROM infractions
                           WHERE case_id = $1
                           AND guild_id = $2;"""

            cases = await con.fetch(query,
                                    search_id, ctx.guild.id)

            if not cases:
                raise Exceptions.InfractionsNotFound(query=target)

            type_str = {
                -1: "???",
                0: "warning",
                1: "mute",
                2: "temp mute",
                3: "soft ban",
                4: "ban",
                5: "temp ban",
                6: "kick"
            }

            await ctx.send(content=utils.dedent(text=f"""🔎 Showing {len(cases[:MAX])}/{len(cases)} found infractions:
                                   ```md
                                   {tabulate(tabular_data=[[
                                                 infraction["case_id"],
                                                 utils.friendly_user(guild=ctx.guild,
                                                                     id=infraction["target_id"]),
                                                 utils.friendly_user(guild=ctx.guild,
                                                                     id=infraction["actor_id"]),
                                                 type_str.get(infraction["type_id"]),
                                                 infraction["reason"],
                                                 infraction["timestamp"].strftime(TS_FORMAT)] for infraction in cases[:MAX
                                            ]],
                                            headers=("ID", "Target", "Actor", "Type", "Reason", "Timestamp"),
                                            tablefmt="simple",
                                            numalign="left", 
                                            stralign="left")}```"""))

    @inf.command(name="recent",
                 usage="inf recent")
    async def inf_recent(self,
                         ctx: commands.Context):
        """Shows the most recent infractions based on their timestamps."""

        MAX = 10
        TS_FORMAT = "%d/%m/%y %H:%M:%S"

        async with postgres.acquire() as con:
            query = """SELECT case_id, target_id, actor_id, type_id, reason, timestamp
                       FROM infractions
                       WHERE guild_id = $1
                       ORDER BY timestamp DESC;"""

            cases = await con.fetch(query,
                                    ctx.guild.id)

            if not cases:
                raise Exceptions.InfractionsNotFound(query=None)

            type_str = {
                -1: "???",
                0: "warning",
                1: "mute",
                2: "temp mute",
                3: "soft ban",
                4: "ban",
                5: "temp ban",
                6: "kick"
            }

            await ctx.send(content=utils.dedent(text=f"""🔎 Showing {len(cases[:MAX])}/{len(cases)} most recent infractions:
                                   ```md
                                   {tabulate(tabular_data=[[
                                                 infraction["case_id"],
                                                 utils.friendly_user(guild=ctx.guild,
                                                                     id=infraction["target_id"]),
                                                 utils.friendly_user(guild=ctx.guild,
                                                                     id=infraction["actor_id"]),
                                                 type_str.get(infraction["type_id"]),
                                                 infraction["reason"],
                                                 infraction["timestamp"].strftime(TS_FORMAT)] for infraction in cases[:MAX
                                            ]],
                                            headers=("ID", "Target", "Actor", "Type", "Reason", "Timestamp"),
                                            tablefmt="simple",
                                            numalign="left", 
                                            stralign="left")}```"""))

    @commands.group(name="lockdown",
                    usage="lockdown <subcommand:text>",
                    aliases=["lock"],
                    invoke_without_command=True)
    async def lockdown(self,
                       ctx: commands.Context):
        """Allows staff to lock or unlock a channel at will."""

        await ctx.send(content=f"🚫 You're missing a subcommand, use **{config.prefix.default}help lockdown** for help.")

    @lockdown.command(name="start",
                      usage="lockdown start [duration:text]")
    @commands.bot_has_permissions(manage_channels=True)
    async def lockdown_start(self,
                             ctx: commands.Context,
                             *, duration: Optional[str] = None):
        """Locks down a channel with an optional duration so that only Mods and Admins can speak."""

        lockdown_config = guilds.get(ctx.guild.id, {}).get("moderation", {}).get("lockdown", {})

        locked_role = lockdown_config.get("locked_role")
        bypassed_roles = list(filter(None.__ne__, [ctx.guild.get_role(role_id=role) for role in lockdown_config.get("bypassed_roles", [])]))

        if locked_role == "everyone":
            locked_role = ctx.guild.default_role

        else:
            locked_role = ctx.guild.get_role(role_id=locked_role)
        
        if locked_role is None:
            raise Exceptions.LockdownRoleNotConfigured()

        if ctx.channel.overwrites_for(obj=locked_role).read_messages is False:
            raise Exceptions.NotPublicChannel()

        if ctx.channel.overwrites_for(obj=locked_role).send_messages is False:
            raise Exceptions.AlreadyLocked()

        overwrites = ctx.channel.overwrites
        for bypassed_role in bypassed_roles:
            if bypassed_role in overwrites.keys():
                overwrite = overwrites[bypassed_role]
                overwrite.send_messages = True
                overwrites[bypassed_role] = overwrite

            else:
                overwrites[bypassed_role] = discord.PermissionOverwrite(send_messages=True)

        if locked_role in overwrites.keys():
            overwrite = overwrites[locked_role]
            overwrite.send_messages = False
            overwrites[locked_role] = overwrite

        else:
            overwrites[locked_role] = discord.PermissionOverwrite(send_messages=False)

        await ctx.channel.edit(reason=f"Lockdown by: {ctx.author}",
                               overwrites=overwrites)

        if duration:
            time_to_wait = await self.DurationConverter().convert(argument=duration)

            if time_to_wait != 0:
                await self.artemis.timer_backend.create_new_timer(artemis=self.artemis,
                                                                  event="lockdown",
                                                                  expire_at=datetime.utcnow() + timedelta(seconds=time_to_wait),
                                                                  extras={
                                                                      "channel": ctx.channel.id
                                                                  })

                friendly_string = utils.time_since(seconds=time_to_wait,
                                                   pretty=True,
                                                   ms=False,
                                                   granularity=7,
                                                   skip_empty=True)

                self.artemis.dispatch(event_name="logging_action",
                                      guild=ctx.guild,
                                      action="LOCKDOWN_TEMP",
                            
                                      channel=ctx.channel,
                                      actor=ctx.author,
                                      duration=friendly_string)

                return await ctx.send(content=f"{emojis.tick_yes} Lockdown has been activated for {friendly_string}.\n**Use -lockdown end to cancel lockdown.**")

        self.artemis.dispatch(event_name="logging_action",
                              guild=ctx.guild,
                              action="LOCKDOWN",
                            
                              channel=ctx.channel,
                              actor=ctx.author)

        await ctx.send(content=f"{emojis.tick_yes} Lockdown has been activated.\n**Use -lockdown end to cancel lockdown.**")

    @lockdown.command(name="end",
                      usage="lockdown end")
    @commands.bot_has_permissions(manage_channels=True)
    async def lockdown_end(self,
                           ctx: commands.Context):
        """Ends an active lockdown in the current channel."""

        lockdown_config = guilds.get(ctx.guild.id, {}).get("moderation", {}).get("lockdown", {})

        locked_role = lockdown_config.get("locked_role")
        bypassed_roles = list(filter(None.__ne__, [ctx.guild.get_role(role_id=role) for role in lockdown_config.get("bypassed_roles", [])]))

        if locked_role == "everyone":
            locked_role = ctx.guild.default_role

        else:
            locked_role = ctx.guild.get_role(role_id=locked_role)
        
        if locked_role is None:
            raise Exceptions.LockdownRoleNotConfigured()

        if ctx.channel.overwrites_for(obj=locked_role).read_messages is False:
            raise Exceptions.NotPublicChannel()

        if ctx.channel.overwrites_for(obj=locked_role).send_messages in (True, None):
            raise Exceptions.NotLocked()

        overwrites = ctx.channel.overwrites
        for bypassed_role in bypassed_roles:
            if bypassed_role in overwrites.keys():
                overwrite = overwrites[bypassed_role]
                overwrite.send_messages = None
                overwrites[bypassed_role] = overwrite

            else:
                overwrites[bypassed_role] = discord.PermissionOverwrite(send_messages=None)

        if locked_role in overwrites.keys():
            overwrite = overwrites[locked_role]
            overwrite.send_messages = None
            overwrites[locked_role] = overwrite

        else:
            overwrites[locked_role] = discord.PermissionOverwrite(send_messages=None)

        await ctx.channel.edit(reason=f"Lockdown ended by: {ctx.author}",
                               overwrites=overwrites)

        expiring_timer = self.artemis.timer_backend.get_running_timer(event="lockdown",
                                                                      query={
                                                                          "channel": ctx.channel.id
                                                                      })

        if expiring_timer is not None:
            await expiring_timer.cancel()

        self.artemis.dispatch(event_name="logging_action",
                              guild=ctx.guild,
                              action="LOCKDOWN_CANCEL",
                            
                              channel=ctx.channel,
                              actor=ctx.author)

        await ctx.send(content=f"{emojis.tick_yes} Lockdown has been cancelled.")


class Exceptions(blueprint, commands.Cog, name="Moderation Exceptions"):
    """This is a collection of exceptions raised only in this file.
    
    This cog also comes equipped with its own command error listener."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    
    class AlreadyBanned(ArtemisException):
        def __init__(self,
                     user: Union[discord.Member, discord.User],
                     *, reason: Optional[str] = None):
            self.user = user
            self.reason = reason


    class AlreadyMuted(ArtemisException):
        def __init__(self,
                     user: discord.Member):
            self.user = user

    
    class BanNotFound(ArtemisException):
        def __init__(self,
                     user: discord.User):
            self.user = user


    class NotMuted(ArtemisException):
        def __init__(self,
                     user: discord.User):
            self.user = user


    class NotLocked(ArtemisException):
        pass


    class AlreadyLocked(ArtemisException):
        pass


    class CannotPunishUser(ArtemisException):
        def __init__(self,
                     user: Union[discord.Member, discord.User],
                     reason: str):
            self.user = user
            self.reason = reason


    class MuteRoleNotConfigured(ArtemisException):
        pass


    class LockdownRoleNotConfigured(ArtemisException):
        pass


    class NotPublicChannel(ArtemisException):
        pass


    class InfractionsNotFound(ArtemisException):
        def __init__(self,
                     query: Union[discord.User, int]):
            self.query = query


    class ImproperDuration(ArtemisException):
        pass


    class MissingLockdownExpirePerms(ArtemisException):
        pass


    class DurationRequired(ArtemisException):
        pass

    
    @commands.Cog.listener()
    async def on_command_error(self,
                               ctx: commands.Context,
                               error: Any):
        """This handles the error responses for when exceptions listed in this cog are raised."""
    
        if isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, self.CannotPunishUser):
                return await ctx.send(content=f"🚫 You cannot {ctx.command.name} {error.original.user}.")

            if isinstance(error.original, self.AlreadyBanned):
                return await ctx.send(content=f"🙁 {error.original.user} has already been banned.")

            if isinstance(error.original, self.AlreadyMuted):
                return await ctx.send(content=f"🙁 {error.original.user} has already been muted.")

            if isinstance(error.original, self.AlreadyLocked):
                return await ctx.send(content=f"🙁 This channel is already in lockdown.")

            if isinstance(error.original, self.BanNotFound):
                return await ctx.send(content=f"🙁 {error.original.user} has not been banned yet.")

            if isinstance(error.original, self.NotMuted):
                return await ctx.send(content=f"🙁 {error.original.user} has not been muted yet.")

            if isinstance(error.original, self.AlreadyLocked):
                return await ctx.send(content=f"🙁 This channel hasn't been locked down yet.")

            if isinstance(error.original, self.InfractionsNotFound):
                return await ctx.send(content=f"🚫 Couldn't find any infractions matching your query.")

            if isinstance(error.original, (self.ImproperDuration, self.DurationRequired)):
                return await ctx.send(content=f"🚫 Improper duration provided.")

            if isinstance(error.original, self.MuteRoleNotConfigured):
                return await ctx.send(content=f"🚫 This server doesn't have a configured Muted role.")

            if isinstance(error.original, self.LockdownRoleNotConfigured):
                return await ctx.send(content=f"🚫 This server doesn't have a configured role to lock.")

            if isinstance(error.original, self.NotPublicChannel):
                return await ctx.send(content=f"🚫 This channel is not public.")

            if isinstance(error.original, self.MissingLockdownExpirePerms):
                return await ctx.send(content=f"🚫 Lockdown expired here but I don't have permissions to remove it.\n**Give me the Manage Channels permission then run -lockdown end to cancel lockdown.**")


class Listeners(blueprint, commands.Cog, name="Moderation Listeners"):
    """These listeners typically handle automation of basic moderation functionality.
    
    The prime example is auto role and auto mod."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    async def respond(self,
                      action: int,
                      message: discord.Message,
                      reason: str):
        """Dispatches a response to an auto mod infraction.
        
        This uses a sort of exponential back-off system in the event that a configured action can't be taken due to incorrect permissions.
        For example, if a ban isn't possible, we try to kick, if that fails then do a mute etc, etc."""

        if action == 4:
            return

        if action == 0:
            if message.guild.me.guild_permissions.ban_members:
                await message.author.ban(reason=f"Automod: {reason}")

            else:
                action = 1

        if action == 1:
            if message.guild.me.guild_permissions.kick_members:
                await message.author.kick(reason=f"Automod: {reason}")

            else:
                action = 2

        if action == 2:
            role = message.guild.get_role(role_id=guilds.get(message.guild.id, {}).get("moderation", {}).get("mute_role"))
            if message.guild.me.guild_permissions.manage_roles or role is None:
                await message.author.add_roles(role, 
                                               reason=f"Automod: {reason}")

            else:
                action = 3

        type_id = {
            0: "BAN",
            1: "KICK",
            2: "MUTE",
            3: "WARN"
        }.get(action, "BAN")

        await new_infraction(artemis=self.artemis,
                             guild=message.guild,
                             actor=self.artemis.user,
                             target=message.author,
                             reason=reason,
                             type=type_id)

    @commands.Cog.listener(name="on_message")
    async def anti_spam(self,
                        message: discord.Message):
        """This handles anti spam for the particular server."""

        if message.guild is None or message.author == self.artemis.user:
            return

        spam_config = guilds.get(message.guild.id, {}).get("anti", {}).get("spam", {})
        
        if not spam_config.get("enabled", False):
            return
        
        max_count = spam_config.get("count", 5)
        threshold = spam_config.get("threshold", 5)

        if message.channel.id in spam_config.get("bypassed_channels", []) or utils.first(iterable=spam_config.get("bypassed_roles", []),
                                                                                         condition=lambda r: r in (role.id for role in message.author.roles)):
            return

        count = redis.incr(f"spam:{message.guild.id}:{message.author.id}")
        redis.expire(f"spam:{message.guild.id}:{message.author.id}", threshold)

        if count > max_count - 1:
            await self.respond(action=spam_config.get("action", 0),
                               message=message,
                               reason=f"Spam detected in #{message.channel} ({max_count}/{threshold}s)")

            if message.guild.me.guild_permissions.manage_messages:
                await message.channel.purge(limit=max_count,
                                            check=lambda m: m.author == message.author)

    @commands.Cog.listener(name="on_message")
    async def anti_pings(self,
                         message: discord.Message):
        """This handles anti ping spam for the particular server."""

        if message.guild is None or message.author == self.artemis.user or not message.mentions:
            return

        ping_spam_config = guilds.get(message.guild.id, {}).get("anti", {}).get("pings", {})
        
        if not ping_spam_config.get("enabled", False):
            return
        
        max_count = ping_spam_config.get("count", 5)
        threshold = ping_spam_config.get("threshold", 5)

        if message.channel.id in ping_spam_config.get("bypassed_channels", []) or utils.first(iterable=ping_spam_config.get("bypassed_roles", []),
                                                                                              condition=lambda r: r in (role.id for role in message.author.roles)):
            return

        count = redis.incr(f"ping:{message.guild.id}:{message.author.id}")
        redis.expire(f"ping:{message.guild.id}:{message.author.id}", threshold)

        if count > max_count - 1:
            await self.respond(action=ping_spam_config.get("action", 0),
                               message=message,
                               reason=f"Ping spam detected in #{message.channel} ({max_count}/{threshold}s)")

    @commands.Cog.listener(name="on_message")
    async def anti_invite(self,
                          message: discord.Message):
        """This handles anti invite for the particular server."""

        if message.guild is None or message.author == self.artemis.user:
            return

        invite_config = guilds.get(message.guild.id, {}).get("anti", {}).get("invite", {})
        
        if not invite_config.get("enabled", False):
            return

        if message.channel.id in invite_config.get("bypassed_channels", []) or utils.first(iterable=invite_config.get("bypassed_roles", []),
                                                                                           condition=lambda r: r in (role.id for role in message.author.roles)):
            return

        REGEX = r"(https?:\/\/)?(www\.)?(discord|invite\.(gg|io|me|li)|discordapp\.com\/invite)\/.+[a-z]"
        whitelisted_partial = "|".join(whitelist for whitelist in invite_config.get("whitelist", []))
        match = [m.group() for m in finditer(REGEX, message.content, IGNORECASE)]

        if not match:
            return

        if message.guild.me.guild_permissions.manage_guild:
            invites = "|".join(invite.code for invite in await message.guild.invites())

        for invite in match[0].split(" "):
            if not search(REGEX, invite, IGNORECASE):
                continue

            if whitelisted_partial:
                if search(rf"(https?:\/\/)?(www\.)?(discord|invite\.(gg|io|me|li)|discordapp\.com\/invite)\/({whitelisted_partial})", invite, IGNORECASE):
                    continue

            if message.guild.me.guild_permissions.manage_guild:
                if search(rf"(https?:\/\/)?(www\.)?(discord|invite\.(gg|io|me|li)|discordapp\.com\/invite)\/({invites})", invite, IGNORECASE) and invites:
                    continue

            await self.respond(action=invite_config.get("action", 0),
                               message=message,
                               reason=f"Invite detected in #{message.channel}")

            if message.guild.me.guild_permissions.manage_messages:
                await message.delete()

            break

    @commands.Cog.listener()
    async def on_member_join(self,
                             member: discord.Member):
        """Automatically adds auto roles to users when they join the server."""

        if member.bot:
            key = "BOT"
        
        else:
            key = "HUMAN"

        roles = list(filter(None.__ne__, [member.guild.get_role(role_id=role[0]) for role in utils.all(iterable=guilds.get(member.guild.id, {}).get("moderation", {}).get("auto_roles", {}).items(),
                                                                                                       condition=lambda r: key in r[1])]))

        await member.add_roles(*roles)
        console.debug(text=f"Added {len(roles)} auto roles to {member}.")

    @commands.Cog.listener()
    async def on_lockdown_expire(self,
                                 channel: int):
        """Handles a response to when a lockdown expires."""

        channel = self.artemis.get_channel(id=channel)

        if channel.guild.me.guild_permissions.manage_channels is False:
            raise Exceptions.MissingLockdownExpirePerms()

        lockdown_config = guilds.get(channel.guild.id, {}).get("moderation", {}).get("lockdown", {})

        locked_role = lockdown_config.get("locked_role")
        bypassed_roles = list(filter(None.__ne__, [channel.guild.get_role(role_id=role) for role in lockdown_config.get("bypassed_roles", [])]))

        if locked_role == "everyone":
            locked_role = channel.guild.default_role

        else:
            locked_role = channel.guild.get_role(role_id=locked_role)
        
        if locked_role is None:
            return

        if channel.overwrites_for(obj=locked_role).read_messages is False:
            return

        if channel.overwrites_for(obj=locked_role).send_messages in (True, None):
            return

        overwrites = channel.overwrites
        for bypassed_role in bypassed_roles:
            if bypassed_role in overwrites.keys():
                overwrite = overwrites[bypassed_role]
                overwrite.send_messages = None
                overwrites[bypassed_role] = overwrite

            else:
                overwrites[bypassed_role] = discord.PermissionOverwrite(send_messages=None)

        if locked_role in overwrites.keys():
            overwrite = overwrites[locked_role]
            overwrite.send_messages = None
            overwrites[locked_role] = overwrite

        else:
            overwrites[locked_role] = discord.PermissionOverwrite(send_messages=None)

        await channel.edit(reason=f"Lockdown expired.",
                           overwrites=overwrites)

        await channel.send(content=f"🚨 Lockdown has expired, chat has been unlocked.")

        self.artemis.dispatch(event_name="logging_action",
                              guild=channel.guild,
                              action="LOCKDOWN_EXPIRE",
                            
                              channel=channel)
                              
    @commands.Cog.listener()
    async def on_temp_mute_expire(self,
                                  target: int,
                                  guild: int,
                                  case: int):
        """Handles auto unmute for temp mutes."""
        
        guild = self.artemis.get_guild(id=guild)
        member = guild.get_member(user_id=target)

        if not guild.me.guild_permissions.manage_roles:
            return

        guild_config = guilds.get(guild.id, {}).get("moderation", {})
        role = guild.get_role(role_id=guild_config.get("mute_role"))

        if role is None:
            return

        if member:
            if role not in member.roles:
                return

            await member.remove_roles(role,
                                      reason="Temp mute expired.")

        else:
            member = await self.artemis.fetch_user(user_id=target)

            if member is None:
                return

            if guild_config.get("persistent_roles", {}).get("enabled", False):
                async with postgres.acquire() as con:
                    query = """SELECT role_ids
                               FROM persistent_roles
                               WHERE user_id = $1
                               AND guild_id = $2;"""

                    persistent_roles = await con.fetchval(query,
                                                          member.id, guild.id)

                    if persistent_roles:
                        roles_as_list = utils.string_list(string=persistent_roles)
                        roles_as_list.remove(role.id)

                        query = """UPDATE persistent_roles
                                   SET role_ids = $1
                                   WHERE user_id = $2
                                   AND guild_id = $3;"""

                        await con.execute(query,
                                          str(roles_as_list), member.id, guild.id)

        self.artemis.dispatch(event_name="logging_action",
                              guild=guild,
                              action="MEMBER_MUTE_EXPIRE",
                                
                              user=member,
                              case=case)

    @commands.Cog.listener()
    async def on_temp_ban_expire(self,
                                 target: int,
                                 guild: int,
                                 case: int):
        """Handles auto unban for temp bans."""
        
        guild = self.artemis.get_guild(id=guild)

        if not guild.me.guild_permissions.ban_members:
            return

        target = await self.artemis.fetch_user(user_id=target)

        if target is None:
            return

        try:
            await guild.unban(user=target,
                              reason="Temp ban expired.")

            self.artemis.dispatch(event_name="logging_action",
                                  guild=guild,
                                  action="MEMBER_BAN_EXPIRE",
                                    
                                  user=target,
                                  case=case)

        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_member_unban(self,
                              guild: discord.Guild,
                              user: discord.User):
        """This handles the clearing of any running temp ban timers when a user is unbanned."""

        expiring_timer = self.artemis.timer_backend.get_running_timer(event="temp_ban",
                                                                      query={
                                                                          "target": user.id,
                                                                          "guild": guild.id
                                                                      })

        if expiring_timer is not None:
            console.debug(text=f"Prematurely cancelling task {expiring_timer.id} because they were unmuted before it expired.")

            await expiring_timer.cancel()

    @commands.Cog.listener(name="on_member_update")
    async def auto_temp_cancel(self,
                               before: discord.Member,
                               after: discord.Member):
        """Cancels any running temp mute timers when the mute role is removed."""

        if before.roles == after.roles:
            return 

        guild_config = guilds.get(after.guild.id, {}).get("moderation", {})
        role = after.guild.get_role(role_id=guild_config.get("mute_role"))

        if role is None:
            return

        if role not in after.roles and role in before.roles:
            expiring_timer = self.artemis.timer_backend.get_running_timer(event="temp_mute",
                                                                          query={
                                                                              "target": after.id,
                                                                              "guild": after.guild.id
                                                                          })

            if expiring_timer is not None:
                console.debug(text=f"Prematurely cancelling task {expiring_timer.id} because they were unmuted before it expired.")

                await expiring_timer.cancel()
            
            if guild_config.get("persistent_roles", {}).get("enabled", False):
                async with postgres.acquire() as con:
                    query = """SELECT role_ids
                               FROM persistent_roles
                               WHERE user_id = $1
                               AND guild_id = $2;"""

                    persistent_roles = await con.fetchval(query,
                                                          after.id, after.guild.id)

                    if persistent_roles:
                        roles_as_list = utils.string_list(string=persistent_roles)
                        try:
                            roles_as_list.remove(role.id)

                        except:
                            pass

                        query = """UPDATE persistent_roles
                                   SET role_ids = $1
                                   WHERE user_id = $2
                                   AND guild_id = $3;"""

                        await con.execute(query,
                                          str(roles_as_list), after.id, after.guild.id)


LOCAL_COGS = [
    Commands,
    Exceptions,
    Listeners
]


def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")