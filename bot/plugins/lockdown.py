import discord

import ext.state as state

from datetime import datetime, timedelta
from discord.ext import commands

from ext.converters import DurationConverter
from ext.exceptions import CustomException, MissingSubcommand, NotConfigured
from ext.state import access_control
from ext.utils import time_since

from plugins.logging import Handler as LoggingHandler


class AlreadyLocked(CustomException):
	pass

class NotLocked(CustomException):
	pass

class PrivateChannel(CustomException):
	pass

class Config:
	def __init__(self, bot, guild):
		self.bot = bot
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id, {}).get("lockdown", {})

		raw_role = self.raw.get("locked_role", "everyone")

		if raw_role in ("everyone", "@everyone"):
			self.role = self.guild.default_role

		else:
			self.role = self.guild.get_role(raw_role)
		
		self.whitelist = list(filter(None, [self.guild.get_role(r) for r in self.raw.get("whitelist", [])]))

	async def start(self, actor, channel, duration=None):
		if not channel.permissions_for(channel.guild.me).manage_channels:
			raise commands.BotMissingPermissions(["manage_channels"])

		if self.role is None:
			raise NotConfigured("lockdown.locked_role")

		if channel.overwrites_for(self.role).read_messages is False:
			raise PrivateChannel()

		if channel.overwrites_for(self.role).send_messages is False:
			raise AlreadyLocked()

		overwrites = channel.overwrites
		for role in self.whitelist:
			if role in overwrites.keys():
				overwrite = overwrites[role]
				overwrite.send_messages = True
				overwrites[role] = overwrite

			else:
				overwrites[role] = discord.PermissionOverwrite(send_messages=True)

		if self.role in overwrites.keys():
			overwrite = overwrites[self.role]
			overwrite.send_messages = False
			overwrites[self.role] = overwrite

		else:
			overwrites[self.role] = discord.PermissionOverwrite(send_messages=False)

		await channel.edit(
			overwrites=overwrites,
			reason=f"Lockdown by: {actor}"
		)

		if duration is not None:
			await state.timer_handler.new(
				event="lockdown",
				expire_at=datetime.utcnow() + timedelta(seconds=duration),
				extras={"channel_id": channel.id}
			)

		await LoggingHandler(self.bot, self.guild).dispatch("LOCKDOWN_TEMP" if duration is not None else "LOCKDOWN",
			actor=actor,
			channel=channel,
			duration=time_since(seconds=duration) if duration is not None else None
		)

	async def end(self, actor, channel, expired=False):
		if not channel.permissions_for(channel.guild.me).manage_channels:
			raise commands.BotMissingPermissions(["manage_channels"])

		if self.role is None:
			raise NotConfigured("lockdown.locked_role")

		if channel.overwrites_for(obj=self.role).read_messages is False:
			raise PrivateChannel()

		if channel.overwrites_for(obj=self.role).send_messages in (True, None):
			raise NotLocked()

		overwrites = channel.overwrites
		for role in self.whitelist:
			if role in overwrites.keys():
				overwrite = overwrites[role]
				overwrite.send_messages = None
				overwrites[role] = overwrite

			else:
				overwrites[role] = discord.PermissionOverwrite(send_messages=None)

		if self.role in overwrites.keys():
			overwrite = overwrites[self.role]
			overwrite.send_messages = None
			overwrites[self.role] = overwrite

		else:
			overwrites[self.role] = discord.PermissionOverwrite(send_messages=None)

		await channel.edit(
			reason=f"Lockdown ended by: {actor}",
			overwrites=overwrites
		)

		expiring_timer = state.timer_handler.get("lockdown", {"channel": channel.id})

		if expiring_timer is not None:
			await expiring_timer.cancel()

		await LoggingHandler(self.bot, self.guild).dispatch("LOCKDOWN_EXPIRE" if expired else "LOCKDOWN_CANCEL",
			actor=actor,
			channel=channel
		)


class Plugin(commands.Cog, name="Channel Lockdown"):
	"""Often used during raids, the lockdown commands allow Administrators to lock a channel for any length of time or until manually cancelled.

	As mentioned previously, the is especially helpful during raids when a few channels are being bombarded with messages. Using lockdown prevents anyone with the configured role from talking in that channel.

	It should be noted that lockdown cannot be initiated in a channel where the configured `locked_role` cannot read messages. This is to prevent a situation where staff chats become visible to regular members."""

	def __init__(self, bot):
		self.bot = bot

	async def error_handler(self, ctx, error, res):
		if isinstance(error, commands.CommandInvokeError):
			if isinstance(error.original, AlreadyLocked):
				await res("The channel is already in lockdown.")
				return True

			if isinstance(error.original, NotLocked):
				await res("The channel hasn't been locked yet.")
				return True

			if isinstance(error.original, PrivateChannel):
				await res("Hidden channels can't be locked.")
				return True

		return False

	@commands.group("lockdown",
		usage="lockdown",
		invoke_without_command=True
	)
	async def lockdown(self, ctx):
		"""Allows admins to lock and unlock channels."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.ADMIN)
	@lockdown.command("start",
		usage="lockdown start [duration:text]"
	)
	@commands.bot_has_permissions(manage_channels=True)
	async def lockdown_start(self, ctx, *, duration: DurationConverter = None):
		"""Starts a lockdown in the current channel with an optional duration."""

		await Config(self.bot, ctx.guild).start(ctx.author, ctx.channel, duration)
		
		if duration is not None:
			return await ctx.success(f"Lockdown has been activated for {time_since(seconds=duration)}.\n**Use `lockdown end` to cancel lockdown.**")

		await ctx.success(f"Lockdown has been activated.\n**Use `lockdown end` to cancel lockdown.**")

	@access_control.require(access_control.Level.ADMIN)
	@lockdown.command("end",
		usage="lockdown end"
	)
	@commands.bot_has_permissions(manage_channels=True)
	async def lockdown_end(self, ctx):
		"""Ends an existing lockdown on the current channel."""

		await Config(self.bot, ctx.guild).end(ctx.author, ctx.channel)
		await ctx.success("Lockdown has been cancelled.")

	@commands.Cog.listener()
	async def on_lockdown_expire(self, channel_id):
		channel = self.bot.get_channel(channel_id)

		if channel is None:
			return

		try:
			await Config(self.bot, channel.guild).end(channel.guild.me, channel, True)
		
		except NotLocked:
			return

		except:
			return await channel.send("🚫 Lockdown expired here but something went wrong.\n**Check my permissions and the guild's config, then run `lockdown end` to cancel lockdown.**")
		
		await channel.send(f"🚨 Lockdown has expired, chat has been unlocked.")


def setup(bot):
	cog = Plugin(bot)
	bot.add_cog(cog)
	bot.dispatch("cog_load", cog)