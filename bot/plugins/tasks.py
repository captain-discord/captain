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
from discord.ext import commands, tasks

# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint
from util import console
from util.constants import cache, config


class Tasks(blueprint, commands.Cog, name="Global Tasks"):
    """These tasks handle basic functionality of the bot. 
    
    They perform tasks such as updating APIs and populating Redis."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis
        self.tasks = ["presence_maintainer"]

        for task in self.tasks:
            task_func = getattr(self, task)
            
            if task_func is None:
                console.warn(text=f"Tried to start {task} task but it doesn't exist.")
                continue

            task_func.start()
            console.debug(text=f"Successfully started {task} task.")

    def cog_unload(self):
        for task in self.tasks:
            task_func = getattr(self, task)

            if task_func is None:
                console.warn(text=f"Tried to stop {task} task but it doesn't exist.")
                continue

            if not task_func.is_running():
                console.warn(text=f"Tried to stop {task} task but it isn't running.")

            task_func.stop()
            console.debug(text=f"Successfully stopped {task} task.")

    @tasks.loop(seconds=config.presence.send_every)
    async def presence_maintainer(self):
        """This maintains the bot's presence across the cluster's available shards.
        
        Naturally, Discord likes to reset a bot's presence every few minutes.
        So we need to set it every few minutes to avoid the status disappearing."""

        await cache.presence.set_presence(artemis=self.artemis)

    @presence_maintainer.before_loop
    async def presence_maintainer_wait(self):
        console.debug(text="Waiting until ready before starting the presence_maintainer task.")
        await self.artemis.wait_until_ready()


LOCAL_COGS = [
    Tasks
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")