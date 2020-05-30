# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Any, List


# --------------------
# Builtin dependencies
# --------------------
from asyncio import sleep

# ------------------------
# Third-party dependencies
# ------------------------
from discord import Embed
from discord.ext import commands

# ======================
# Import local libraries
# ======================
import menus as menus
import util.utilities as utils

from custos import blueprint
from util import console, embed
from util.blueprints import CommandSet
from util.constants import config
from util.exceptions import ArtemisException


class Commands(blueprint, commands.Cog, name="Help Command", command_attrs=dict(hidden=True)):
    """Displays the help menu.
    
    The follow reactions are used to interact with the help menu:
    ◀ Move to the previous page.
    ▶ Move to the next page.
    ⏹️ Stop the interactive session.
    ❔ Show the usage help page."""

    def __init__(self, 
                 artemis: Artemis):
        self.artemis = artemis

    class HelpSource(menus.GroupByPageSource):
        def __init__(self,
                     command_sets: List[CommandSet],
                     help_usage: str):
            self.help_usage = help_usage

            super().__init__(entries=command_sets,
                             per_page=1,
                             key=None,
                             sort=False)

        async def format_page(self, 
                              menu: menus.MenuPages, 
                              entry: menus._GroupByEntry) -> Embed:
            command_set = entry.items[0]

            new_embed = Embed(colour=0x36393f,
                              title=command_set.name,
                              description=command_set.description)
            
            new_embed.set_author(name=f"Page {menu.current_page + 1}/{self.get_max_pages()} ({len(command_set.commands)} commands)")

            new_embed.set_footer(text=f"Use {config.prefix.default}{self.help_usage} for more help.")

            for command in command_set.commands:
                description = command.short_doc

                if hasattr(command.callback, "__commands_cooldown__"):
                    cooldown = command.callback.__commands_cooldown__
                    
                    cooldown_type = {
                        commands.BucketType.default: "at any time",
                        commands.BucketType.user: "per user",
                        commands.BucketType.channel: "per channel",
                        commands.BucketType.guild: "per server",
                        commands.BucketType.category: "per channel category",
                        commands.BucketType.member: "per server member",
                        commands.BucketType.role: "per server role",
                    }[cooldown.type]

                    description += f"\n\n**Cooldown: {cooldown.rate} every {utils.time_since(seconds=cooldown.per, pretty=True, skip_empty=True, ms=False)} {cooldown_type}**"

                new_embed.add_field(name=command.usage,
                                    value=description,
                                    inline=False)

            return new_embed


    class HelpMenu(menus.MenuPages):
        def __init__(self,
                     source: List[CommandSet]):
            super().__init__(source=source, 
                             clear_reactions_after=True)

    @commands.group(name="help",
                    usage="help [command|category:text]",
                    invoke_without_command=True)
    async def help(self, 
                   ctx: commands.Context,
                   *, command_lookup: str = None):
        """Displays an interactive help session where users can navigate between different plugins.
        
        If a command name is a provided, a command lookup is ran and the found command is displayed along with its full help string.
        If the provided command name belongs to a command group, then all subcommands in that group are displayed in pages of 5 subcommands each."""

        command_sets = []
        if command_lookup is None:
            for cog_name in self.artemis.cogs:
                cog = self.artemis.get_cog(name=cog_name)
                cog_commands = [command for command in cog.get_commands() if not command.hidden]

                if len(cog_commands) == 0:
                    continue

                command_sets.append(CommandSet(container=cog))

        else:
            found = self.artemis.get_command(name=command_lookup)

            if found is None:
                raise Exceptions.LookupFailed(query=command_lookup)

            command_sets.append(CommandSet(container=found))

        await self.HelpMenu(source=self.HelpSource(command_sets=command_sets,
                                                   help_usage=ctx.command.usage)).start(ctx)


class Exceptions(blueprint, commands.Cog, name="Help Exceptions"):
    """This is a collection of exceptions raised only in this file.
    
    This cog also comes equipped with its own command error listener."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    
    class LookupFailed(ArtemisException):
        def __init__(self,
                     query: str):
            self.query = query


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