# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from discord import Guild, Member
from typing import Any


# ------------------------
# Third-party dependencies
# ------------------------
from discord.ext import commands

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from custos import blueprint

from util import console
from util.constants import config, guilds


class Checks(blueprint, commands.Cog, name="Global Checks"):
    """This cog handles a number of checks that apply to every command in the bot."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

        self.checks = ["is_configured",
                       "can_use"]

        for check in self.checks:
            check_func = getattr(self, check)
            
            if check_func is None:
                console.warn(text=f"Tried to add {check} check but it doesn't exist.")
                continue

            self.artemis.add_check(check_func)
            console.debug(text=f"Successfully added {check} check.")

    def cog_unload(self):
        for check in self.checks:
            check_func = getattr(self, check)

            if check_func is None:
                console.warn(text=f"Tried to remove {check} check but it doesn't exist.")
                continue

            self.artemis.remove_check(check_func)
            console.debug(text=f"Successfully removed {check} check.")

    async def is_configured(self,
                            ctx: commands.Context) -> bool:
        """Globally blocks DM commands as well as refusing to work if the bot does not have a configuration for the current guild."""

        if ctx.guild is None:
            raise commands.NoPrivateMessage()

        if await self.artemis.is_owner(user=ctx.author):
            return True

        guild_config = guilds.get(ctx.guild.id, {})
        if not guild_config:
            raise Exceptions.GuildNotConfigured(guild=ctx.guild)

        return True

    async def can_use(self,
                      ctx: commands.Context) -> bool:
        """This monstrosity checks to see if the user has any roles that allow them to use the command.
        
        Users marked as bot owners completely bypass this check."""

        if await self.artemis.is_owner(user=ctx.author):
            return True

        COMMANDS = {
            0: [command.name for command in self.artemis.commands],
            90: [
                "ban",
                "unban",
                "softban",
                "tempban",

                "kick",
                "warn",

                "mute",
                "unmute",
                "tempmute",

                "purge",
                "purge channel",
                "purge user",
                "purge bots",
                "purge here"
            ],
            100: [
                "lockdown"
            ]
        }

        for command_set in COMMANDS.values():
            if command_set == COMMANDS[0]:
                continue

            for command in COMMANDS[0]:
                if command in command_set:
                    COMMANDS[0].remove(command)

        COMMANDS[90] += COMMANDS[0]
        COMMANDS[100] += COMMANDS[90]

        role_config = guilds.get(ctx.guild.id, {}).get("roles", {})

        roles = utils.all(iterable=role_config.items(),
                          condition=lambda r: r[0] in (role.id for role in ctx.author.roles))
        
        if "everyone" in role_config.keys():
            roles.append(("everyone", role_config.get("everyone", {"level": 0})))

        levels = [role[1].get("level", 0) for role in roles]
        if not levels:
            raise Exceptions.LevelTooLow(user=ctx.author,
                                         level=-1)
        
        max_level = max(levels)
        current_perms = COMMANDS.get(max_level, COMMANDS[0])

        for role in roles:
            for cmd, has in role[1].get("overwrites", {}).items():
                if has == True and cmd not in current_perms:
                    current_perms.append(cmd)
                
                if has == False and cmd in current_perms:
                    current_perms.remove(cmd)

        if ctx.command.name not in current_perms:
            raise Exceptions.LevelTooLow(user=ctx.author,
                                         level=max_level)

        return True


class Exceptions(blueprint, commands.Cog, name="Check Exceptions"):
    """These provide custom responses to certain check failures, making it easier for people to see what went wrong."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis


    class LevelTooLow(commands.CheckFailure):
        def __init__(self,
                     user: Member,
                     level: int):
            self.user = user
            self.level = level

    
    class GuildNotConfigured(commands.CheckFailure):
        def __init__(self,
                     guild: Guild):
            self.guild = guild

    
    @commands.Cog.listener()
    async def on_command_error(self,
                               ctx: commands.Context,
                               error: Any):
        """This handles the error responses for when exceptions listed in this cog are raised."""
    
        if isinstance(error, commands.CheckFailure):
            if isinstance(error, self.GuildNotConfigured):
                return console.warn(text=f"{ctx.author} tried to use a command in an unconfigured guild: {ctx.guild.id}")

            if isinstance(error, self.LevelTooLow):
                return await ctx.send(content=f"🚫 You're not allowed to use that command.")


LOCAL_COGS = [
    Checks,
    Exceptions
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")