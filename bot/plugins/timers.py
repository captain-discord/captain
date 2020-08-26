import discord

import ext.state

from asyncio import sleep
from datetime import datetime, timedelta
from discord.ext import commands
from json import dumps, loads

from ext.utils import first

EVENT_BASE = "{}_expire"

class Timer:
	def __init__(self, bot, **timer_data):
		self.bot = bot
		self.id = timer_data.pop("id", 0)

		self.event = timer_data.pop("event")
		self.extras = timer_data.pop("extras", {})

		self.expire_at = timer_data.pop("expire_at")

		self.cancelled = False

	@classmethod
	async def create(cls, bot, event, expire_at, extras):
		"""Creates a running timer and inserts it into the database.
		
		The extras dict has to be serialised into a string so that Postgres can store it."""

		async with bot.postgres.acquire() as con:
			query = """INSERT INTO timers (event, expire_at, extras) VALUES ($1, $2, $3::jsonb) RETURNING id;"""

			id = await con.fetchval(query, event, expire_at, dumps(extras))

		return cls(bot,
			id=id,
			event=event,
			expire_at=expire_at,
			extras=extras
		)

	async def extend(self, seconds):
		"""Extends a timer by the provided number of seconds."""

		new_time = self.expire_at + timedelta(seconds=seconds)
		self.expire_at = new_time

		async with self.bot.postgres.acquire() as con:
			query = """UPDATE timers SET expire_at = $1 WHERE id = $2;"""
			await con.execute(query, new_time, self.id)

		self.bot.log.debug(f"Extended timer {self.id} to {new_time}.")

	async def start(self):
		"""Starts the current timeout.
		
		If the timer expires, it dispatches an event with all of the extra data."""

		past_expire = self.expire_at
		duration = (past_expire - datetime.utcnow()).total_seconds()

		# we can only sleep reliably for 48 days at a time, let's cap it at 45 just to be safe
		if duration >= 86400 * 45:
			diff = duration - 86400 * 45
			duration -= diff
			await sleep(diff)

		await sleep(duration)

		if self.cancelled:
			return

		if past_expire != self.expire_at:
			return await self.start()

		await self.remove()
		self.dispatch()
		ext.state.timer_handler.running_timers.remove(self)

	async def cancel(self, remove_cache=True):
		"""This cancels the current task.
		
		It doesn't actually interrupt the timeout, it just wipes it from the database and prevents the event from being fired
		if the timer ends.
		
		If remove_cache is provided then the timer is removed from the Timer framework's list of existing timers."""

		self.bot.log.debug(f"Timer {self.id} with event {EVENT_BASE.format(self.event)} has been cancelled.")

		self.cancelled = True
		await self.remove()

		if remove_cache:
			ext.state.timer_handler.running_timers.remove(self)

	async def remove(self):
		"""This removes the timer from the database."""

		async with self.bot.postgres.acquire() as con:
			query = """DELETE FROM timers WHERE id = $1;"""

			await con.execute(query, self.id)

	async def expire(self, force=False):
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

		self.bot.log.debug(f"Dispatched timer {self.id} with event {EVENT_BASE.format(self.event)}.")
		self.bot.dispatch(EVENT_BASE.format(self.event), **self.extras)


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.running_timers = []

	@commands.Cog.listener()
	async def on_ready(self):
		"""This handles the starting of every timer that remains in the database."""

		async with self.bot.postgres.acquire() as con:
			query = """SELECT id, event, expire_at, extras FROM timers;"""
			timers = await con.fetch(query)

		if not timers:
			return self.bot.log.info("There were no timers that needed starting.")

		self.bot.log.info(f"Attempting to start {len(timers)} timers.")
		for timer in timers:
			new_timer = Timer(self.bot,
				id=timer["id"],
				event=timer["event"],
				expire_at=timer["expire_at"],
				extras=loads(timer["extras"])
			)

			self.running_timers.append(new_timer)
			self.bot.log.debug(f"Successfully started a timer for {EVENT_BASE.format(timer['event'])}")

			self.bot.loop.create_task(new_timer.start())

		self.bot.log.info(f"Successfully started {len(self.running_timers)}/{len(timers)} timers.")

	async def new(self, **timer_args):
		"""Creates a new timer and adds it to the cog's cache."""

		new_timer = await Timer.create(self.bot,
			event=timer_args.get("event"),
			expire_at=timer_args.get("expire_at"),
			extras=timer_args.get("extras")
		)

		self.running_timers.append(new_timer)
		self.bot.log.debug(f"Successfully started a timer for {EVENT_BASE.format(timer_args.get('event'))}")
		self.bot.loop.create_task(new_timer.start())

		return new_timer

	def get(self, event, query):
		"""Searches for a running timer with a particular event by an extras value or ID."""

		if isinstance(query, int):
			return first(self.running_timers, lambda timer_set: timer_set.id == query and timer_set.event == event)

		return first(self.running_timers, lambda timer_set: all(item in timer_set.extras.items() for item in query.items()) and timer_set.event == event)

	def get_all(self, event, query):
		"""Returns all running timers that match the provided query."""

		return [t for t in self.running_timers if all(item in t.extras.items() for item in query.items()) and t.event == event]

def setup(bot):
	ext.state.timer_handler = cog = Plugin(bot)
	bot.add_cog(cog)