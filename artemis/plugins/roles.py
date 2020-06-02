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
import util.utilities as utils

from custos import blueprint

from util import console
from util.constants import config, guilds, postgres


class Listeners(blueprint, commands.Cog, name="Persistent Roles"):
    """These listeners handle persistence of roles across rejoins.
    
    This means that users are adaquetly remuted if they leave and rejoin the server."""

    @commands.Cog.listener()
    async def on_member_update(self,
                               before: discord.Member,
                               after: discord.Member):
        """Handles persistent roles for servers."""

        if before.roles == after.roles or not after.guild.me.guild_permissions.manage_roles:
            return 

        if not guilds.get(after.guild.id, {}).get("moderation", {}).get("persistent_roles", {}).get("enabled", False):
            return

        async with postgres.acquire() as con:
            query = """INSERT INTO persistent_roles (user_id, guild_id, role_ids)
                       VALUES ($1, $2, $3)
                       ON CONFLICT ON CONSTRAINT unique_user_guild
                       DO UPDATE
                       SET role_ids = $3;"""

            await con.execute(query,
                              after.id,
                              after.guild.id,
                              str([r.id for r in after.roles]))

            console.debug(text=f"Updated persistent roles for {after.id} in {after.guild.id}.")

    @commands.Cog.listener()
    async def on_member_join(self,
                             member: discord.Member):
        """This adds the persisted roles back to the user."""

        if not member.guild.me.guild_permissions.manage_roles:
            return

        guild_config = guilds.get(member.guild.id, {}).get("moderation", {}).get("persistent_roles", {})
        if not guild_config.get("enabled", False):
            return

        async with postgres.acquire() as con:
            query = """SELECT role_ids
                       FROM persistent_roles
                       WHERE user_id = $1
                       AND guild_id = $2;"""

            roles = await con.fetchval(query,
                                       member.id, member.guild.id)

            if not roles:
                return

        for role in utils.string_list(string=roles):
            if role not in guild_config.get("whitelist", []):
                continue

            role = member.guild.get_role(role_id=role)

            if role in (None, member.guild.default_role):
                continue

            if role.position >= member.guild.me.top_role.position:
                continue

            await member.add_roles(role,
                                   reason="Persisted role.")


LOCAL_COGS = [
    Listeners
]


def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")