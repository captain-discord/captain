import discord, menus

import core.prefix as prefix
import ext.state as state

from datetime import datetime, timedelta
from discord.ext import commands

from ext.converters import DurationConverter
from ext.exceptions import LookupFailed, MissingSubcommand
from ext.state import access_control
from ext.utils import time_since


class ReminderSource(menus.GroupByPageSource):
	def __init__(self, reminders):
		super().__init__(
			entries=reminders,
			per_page=1,
			key=None,
			sort=False
		)

	async def format_page(self, menu, entry):
		reminder = entry.items[0]

		mention_channel = menu.bot.get_channel(reminder.extras.get("channel_id"))
		if mention_channel is None:
			mention_location = "You will be sent a Direct Message once this reminder expires."

		else:
			if not mention_channel.permissions_for(mention_channel.guild.me).send_messages:
				mention_location = "You will be sent a Direct Message once this reminder expires because I can't speak in the channel that you created the reminder in."

			else:
				mention_location = f"You will be mentioned in {mention_channel.mention} once this reminder expires."

		embed = discord.Embed(
			colour=0x7289DA,
			title=f"Reminder #{reminder.id}",
			description=f"{reminder.extras.get('content')}\n\n*{mention_location}*",
			timestamp=reminder.expire_at
		)
		
		embed.set_author(name=f"Page {menu.current_page + 1}/{self.get_max_pages()}")
		embed.set_footer(text="Expires")

		return embed


class Paginator(menus.MenuPages):
	def __init__(self, source):
		super().__init__(
			source=source, 
			clear_reactions_after=True
		)

class Plugin(commands.Cog, name="Reminders"):
	"""If you need to be reminded about something in the future, then you can use the commands below to create, remove and list reminders that you have running!
	
	Once a reminder expires, a message will be sent to the channel which you used the remind command in along with a ping. If the bot cannot speak in that channel, you will be DMed instead."""

	def __init__(self, bot):
		self.bot = bot

	@access_control.require(access_control.Level.DEFAULT)
	@commands.group("reminder",
		usage="reminder",
		aliases=["reminders"],
		invoke_without_command=True
	)
	async def reminder(self, ctx):
		"""Allows users to set a reminder for a certain time in the future."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.DEFAULT)
	@reminder.command("create",
		usage="reminder create <duration:text> <content:text>",
		aliases=["new", "add"]
	)
	async def reminder_create(self, ctx,
		duration: DurationConverter,
		*, content: str
	):
		"""Creates a reminder for something."""

		await state.timer_handler.new(
			event="reminder",
			expire_at=datetime.utcnow() + timedelta(seconds=duration),
			extras={
				"content": content,
				"channel_id": ctx.channel.id,
				"user_id": ctx.author.id
			}
		)
		await ctx.success(f"I've set a reminder {time_since(seconds=duration)} from now for:\n{content}")

	@access_control.require(access_control.Level.DEFAULT)
	@reminder.command("list",
		usage="reminder list",
		aliases=["show", "all"]
	)
	async def reminder_list(self, ctx):
		"""Lists all of a user's currently running reminders."""

		timers = state.timer_handler.get_all("reminder", {"user_id": ctx.author.id})
		if not timers:
			raise LookupFailed("reminders")
		
		await Paginator(ReminderSource(timers)).start(ctx)

	@access_control.require(access_control.Level.DEFAULT)
	@reminder.command("cancel",
		usage="reminder cancel <id:num>",
		aliases=["delete", "remove"]
	)
	async def reminder_cancel(self, ctx,
		id: int
	):
		"""Cancels a currently running reminder."""

		timer = state.timer_handler.get("reminder", id)
		if timer is None:
			raise LookupFailed("reminders")
	
		if timer.extras.get("user_id") != ctx.author.id:
			raise LookupFailed("reminders")			

		await timer.cancel()
		await ctx.success("The reminder has been cancelled.")

	@commands.Cog.listener()
	async def on_reminder_expire(self, user_id, channel_id, content):
		channel = self.bot.get_channel(channel_id)
		user = self.bot.get_user(user_id)
		
		async def send_dm():
			try:
				await user.send(f"Hey there, {user}, here's your reminder for:\n\n{content}\n\n*You received this Direct Message because I couldn't send this message to the channel that you created the reminder in.*")

			except discord.HTTPException:
				return

		if channel is None:
			await send_dm()

		else:
			try:
				await channel.send(f"Hey there, {user.mention}, here's your reminder for:\n\n{content}")

			except discord.HTTPException:
				await send_dm()


def setup(bot):
	bot.add_cog(Plugin(bot))