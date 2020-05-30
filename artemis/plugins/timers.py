# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from bot import Artemis
from typing import Optional, Union


# --------------------
# Builtin dependencies
# --------------------
from asyncio import sleep
from datetime import datetime, timedelta
from json import dumps, loads

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
from util import console, embed
from util.constants import emojis, postgres


EVENT_BASE = "on_{event}_expire"

class Timer(blueprint):
    """Each timer object handles the state of their respective timer and callbacks."""

    def __init__(self,
                 artemis: Artemis,
                 **timer_data: dict):
        self.artemis = artemis
        self.id = timer_data.pop("id", 0)

        self.event = timer_data.pop("event")
        self.extras = timer_data.pop("extras", {})

        self.expire_at = timer_data.pop("expire_at")

        self.cancelled = False

    @classmethod
    async def create(cls,
                     artemis: Artemis,
                     event: str,
                     expire_at: datetime,
                     extras: dict):
        """Creates a running timer and inserts it into the database.
        
        The extras dict has to be serialised into a string so that Postgres can store it."""

        async with postgres.acquire() as con:
            query = """INSERT INTO timers (event, expire_at, extras)
                       VALUES ($1, $2, $3)
                       
                       RETURNING id;"""

            id = await con.fetchval(query,
                                    event, expire_at, dumps(obj=extras))

        return cls(artemis=artemis,
                   id=id,
                   event=event,
                   expire_at=expire_at,
                   extras=extras)

    async def start(self):
        """Starts the current timeout.
        
        If the timer expires, it dispatches an event with all of the extra data."""

        duration = (self.expire_at - datetime.utcnow()).total_seconds()

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # we can only sleep reliably for 48 days at a time,
        # let's cap it at 45 just to be safe
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if duration >= 86400 * 45:
            diff = duration - 86400 * 45
            duration -= diff
            await sleep(delay=diff)

        await sleep(delay=duration)

        if self.cancelled:
            return

        await self.remove()
        self.dispatch()

    async def cancel(self):
        """This cancels the current task.
        
        It doesn't actually interrupt the timeout, it just wipes it from the database and prevents the event from being fired
        if the timer ends."""

        console.debug(text=f"Timer {self.id} with event {EVENT_BASE.format(event=self.event)} has been cancelled.")

        self.cancelled = True
        await self.remove()

    async def remove(self):
        """This removes the timer from the database."""

        async with postgres.acquire() as con:
            query = """DELETE FROM timers
                       WHERE id = $1;"""

            await con.execute(query,
                              self.id)

    async def expire(self,
                     force: Optional[bool] = False):
        """Forces the timer to expire now and dispatch the event.
        
        This also runs cancel() to make sure it doesn't run again.
        If force is provided, the event is dispatched even if the task was cancelled beforehand."""

        if self.cancelled and not force:
            return

        await self.cancel()
        self.dispatch()

    def dispatch(self):
        """Prematurely dispatches the event without touching cancellation or the database.
        
        This shouldn't really be called externally as it will lead to double responses."""

        console.debug(f"Dispatched timer {self.id} with event {EVENT_BASE.format(event=self.event)}.")

        self.artemis.dispatch(event_name=EVENT_BASE[3:].format(event=self.event),
                              **self.extras)


class Backend(blueprint, commands.Cog, name="Timer Backend"):
    """A backend designed to handle cross-restart timers for reminders and temp punishments."""

    def __init__(self,
                 artemis: Artemis):
        self.artemis = artemis
        self.running_timers = []

        self.artemis.timer_backend = self

    @commands.Cog.listener()
    async def on_ready(self):
        """This handles the starting of every timer that remains in the database."""

        async with postgres.acquire() as con:
            query = """SELECT id, event, expire_at, extras
                       FROM timers;"""

            timers = await con.fetch(query)

        if not timers:
            return console.info("There were no timers that needed starting.")

        console.debug(text=f"Attempting to start {len(timers)} timers.")
        for timer in timers:
            new_timer = Timer(artemis=self.artemis,
                              id=timer["id"],
                              event=timer["event"],
                              expire_at=timer["expire_at"],
                              extras=loads(timer["extras"]))

            self.running_timers.append(new_timer)
            console.debug(text=f"Successfully started a timer for {EVENT_BASE.format(event=timer['event'])}")

            self.artemis.loop.create_task(new_timer.start())

        console.info(text=f"Successfully started {len(self.running_timers)}/{len(timers)} timers.")

    async def create_new_timer(self,
                               **timer_args: dict) -> Timer:
        """Creates a new timer and adds it to the cog's cache."""

        new_timer = await Timer.create(artemis=self.artemis,
                                       event=timer_args.get("event"),
                                       expire_at=timer_args.get("expire_at"),
                                       extras=timer_args.get("extras"))

        self.running_timers.append(new_timer)
        console.debug(text=f"Successfully started a timer for {EVENT_BASE.format(event=timer_args.get('event'))}")

        self.artemis.loop.create_task(new_timer.start())

        return new_timer

    def get_running_timer(self,
                          event: str,
                          query: Union[int, dict]) -> Timer:
        """Searches for a running timer with a particular event by an extras value or ID."""

        if isinstance(query, int):
            return utils.first(iterable=self.running_timers,
                               condition=lambda timer_set: timer_set.id == query and timer_set.event == event)

        return utils.first(iterable=self.running_timers,
                           condition=lambda timer_set: all(item in timer_set.extras.items() for item in query.items()) and timer_set.event == event)


LOCAL_COGS = [
    Backend
]

def setup(artemis: Artemis):
    for cog in LOCAL_COGS:
        artemis.add_cog(cog=cog(artemis=artemis))
        console.debug(text=f"Successfully loaded the {cog.__class__.__name__} cog.")