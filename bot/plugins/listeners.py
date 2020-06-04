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
from custos import blueprint

from util import console
from util.constants import cache, guilds, postgres


class Listeners(blueprint, commands.Cog, name="Global Listeners"):
    """This cog is intended for listeners that do not strongly relate to any other modules."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    @commands.Cog.listener()
    async def on_ready(self):
        """This handles some cache population and database synchronisation."""

        if not cache.first_ready_time:
            self.artemis.print_fig()
            cache.first_ready_time = datetime.utcnow()

        console.info(text="Beginning database synchronisation...")
        async with postgres.acquire() as con:
            for guild in self.artemis.guilds:
                if not guild.me.guild_permissions.manage_roles:
                    console.debug(text=f"Skipping synchronisation of {guild.id} because the Manage Roles permission is missing.")

                config = guilds.get(guild.id, {})
                if config is None:
                    console.debug(text=f"Skipping synchronisation of {guild.id} because it is not configured.")
                    continue

                if not config.get("moderation", {}).get("persistent_roles", {}).get("enabled", False):
                    console.debug(text=f"Skipping synchronisation of {guild.id} because persistent roles is disabled.")
                    continue

                console.debug(text=f"Synchronising persistent roles for {guild.id}.")
                if guild.large:
                    console.debug(text=f"Fetching offline members for {guild.id}.")
                    await self.artemis.fetch_offline_members(guild)

                for member in guild.members:
                    query = """INSERT INTO persistent_roles (user_id, guild_id, role_ids)
                               VALUES ($1, $2, $3)
                               ON CONFLICT ON CONSTRAINT unique_user_guild
                               DO UPDATE
                               SET role_ids = $3;"""

                    await con.execute(query,
                                      member.id, guild.id, str([r.id for r in member.roles]))
        
                console.info(text=f"Successfully synchronised persistent roles for {guild.id}.")

        console.info(text="Database synchronisation complete.")


LOCAL_COGS = [
    Listeners
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")