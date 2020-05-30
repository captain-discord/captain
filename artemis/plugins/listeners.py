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
from util.constants import cache


class Listeners(blueprint, commands.Cog, name="Global Listeners"):
    """This cog is intended for listeners that do not strongly relate to any other modules."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis

    @commands.Cog.listener()
    async def on_ready(self):
        """Dictates when the bot knows that it is ready."""

        if not cache.first_ready_time:
            self.artemis.print_fig()
            cache.first_ready_time = datetime.utcnow()


LOCAL_COGS = [
    Listeners
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")