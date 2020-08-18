import discord

import ext.state as state

from ast import literal_eval
from datetime import datetime, timedelta
from discord.ext import commands
from tabulate import tabulate
from typing import Union

from ext.converters import BanCandidateConverter, DurationConverter
from ext.exceptions import AccessDenied, CustomException, LookupFailed, MissingSubcommand, NotConfigured
from ext.state import access_control
from ext.utils import dedent, clean_user, time_since

from plugins.logging import Handler as LoggingHandler

class AlreadyMuted(CustomException):
	pass

class NotMuted(CustomException):
	pass

class CannotPunish(CustomException):
	def __init__(self, reason):
		self.reason = reason

class Handler:
	def __init__(self, bot, guild):
		self.bot = bot
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id).get("infractions", {})

		self.mute_role = self.guild.get_role(self.raw.get("mute_role"))
		self.ban_purge_days = self.raw.get("ban_purge_days", 7)

	async def insert(self, actor, target, event, reason):
		if not isinstance(actor, int):
			actor = actor.id

		if not isinstance(target, int):
			target = target.id

		type_id = {
			"ban": 0,
			"kick": 1,
			"mute": 2,
			"warn": 3
		}.get(event, 0)

		async with self.bot.postgres.acquire() as con:
			query = """INSERT INTO infractions (guild_id, actor_id, target_id, type_id, reason, created_at) 
					   VALUES ($1, $2, $3, $4, $5, $6)
					   
					   RETURNING id;"""

			return await con.fetchval(query, self.guild.id, actor, target, type_id, reason, datetime.utcnow())

	async def timer(self, event, target, case, duration):
		if not isinstance(target, int):
			target = target.id

		await state.timer_handler.new(
			event="temp_" + event,
			expire_at=datetime.utcnow() + timedelta(seconds=duration),
			extras={
				"target_id": target,
				"guild_id": self.guild.id,
				"case_id": case
			}
		)

	async def ban(self, actor, target, reason, duration=None):
		if not self.guild.me.guild_permissions.ban_members:
			raise commands.BotMissingPermissions(["ban_members"])

		if isinstance(target, discord.Member):
			if (target.top_role.position >= actor.top_role.position or self.guild.owner == target) and actor != self.guild.owner:
				raise AccessDenied()

		await self.guild.ban(target,
			reason=f"{actor}: {reason}",
			delete_message_days=self.ban_purge_days
		)

		case = await self.insert(actor, target, "ban", reason)
		log = LoggingHandler(self.bot, self.guild)

		if duration is not None:
			await self.timer("ban", target, case, duration)
			await log.dispatch("MEMBER_TEMPBAN", target,
				target=target,
				actor=actor,
				duration=time_since(seconds=duration),
				reason=reason,
				case=case	
			)

		else:
			await log.dispatch("MEMBER_BAN", target,
				target=target,
				actor=actor,
				reason=reason,
				case=case
			)

		return case

	async def unban(self, actor, target, case=None):
		if not self.guild.me.guild_permissions.ban_members:
			raise commands.BotMissingPermissions(["ban_members"])

		await self.guild.unban(target,
			reason=str(actor),
		)

		if case is not None:
			await LoggingHandler(self.bot, self.guild).dispatch("MEMBER_BAN_EXPIRE", target,
				target=target,
				actor=actor,
				case=case
			)

		else:
			await LoggingHandler(self.bot, self.guild).dispatch("MEMBER_UNBAN", target,
				target=target,
				actor=actor
			)

	async def kick(self, actor, target, reason):
		if not self.guild.me.guild_permissions.kick_members:
			raise commands.BotMissingPermissions(["kick_members"])

		if (target.top_role.position >= actor.top_role.position or self.guild.owner == target) and actor != self.guild.owner:
			raise AccessDenied()

		await self.guild.kick(target,
			reason=f"{actor}: {reason}"
		)

		case = await self.insert(actor, target, "ban", reason)
		await LoggingHandler(self.bot, self.guild).dispatch("MEMBER_KICK", target,
			target=target,
			actor=actor,
			reason=reason,
			case=case
		)

		return case

	async def mute(self, actor, target, reason, duration=None):
		if not self.guild.me.guild_permissions.manage_roles:
			raise commands.BotMissingPermissions(["manage_roles"])

		if self.mute_role is None:
			raise NotConfigured("infractions.mute_role")

		if self.mute_role in target.roles:
			raise AlreadyMuted()

		if (target.top_role.position >= actor.top_role.position or self.guild.owner == target) and actor != self.guild.owner:
			raise AccessDenied()

		await target.add_roles(self.mute_role,
			reason=f"{actor}: {reason}"			
		)

		case = await self.insert(actor, target, "mute", reason)
		log = LoggingHandler(self.bot, self.guild)

		if duration is not None:
			await self.timer("mute", target, case, duration)
			await log.dispatch("MEMBER_TEMPMUTE", target,
				target=target,
				actor=actor,
				duration=time_since(seconds=duration),
				reason=reason,
				case=case	
			)

		else:
			await log.dispatch("MEMBER_MUTE", target,
				target=target,
				actor=actor,
				reason=reason,
				case=case
			)

		return case

	async def unmute(self, actor, target, case=None):
		if not self.guild.me.guild_permissions.manage_roles:
			raise commands.BotMissingPermissions(["manage_roles"])

		if self.mute_role is None:
			raise NotConfigured("infractions.mute_role")

		if (target.top_role.position >= actor.top_role.position or self.guild.owner == target) and actor != self.guild.owner:
			raise AccessDenied()

		await target.remove_roles(self.mute_role,
			reason=str(actor)			
		)

		if case is not None:
			await LoggingHandler(self.bot, self.guild).dispatch("MEMBER_MUTE_EXPIRE", target,
				target=target,
				actor=actor,
				case=case
			)

		else:
			await LoggingHandler(self.bot, self.guild).dispatch("MEMBER_UNMUTE", target,
				target=target,
				actor=actor
			)

	async def warn(self, actor, target, reason):
		if (target.top_role.position >= actor.top_role.position or self.guild.owner == target) and actor != self.guild.owner:
			raise AccessDenied()

		case = await self.insert(actor, target, "warn", reason)
		await LoggingHandler(self.bot, self.guild).dispatch("MEMBER_WARN", target,
			target=target,
			actor=actor,
			reason=reason,
			case=case
		)

		return case


class Plugin(commands.Cog, name="User Infractions"):
	"""The commands displayed below allow people with Moderator permissions to issue punishments to users in a way that's as verbose or as vague as they want it to be.

	Each punishment command takes an optional reason (this does not include commands that undo a punishment i.e. unban/unmute) and has a sister that allows Moderators to issue the punishment for a set amount of time.
	Temporary punishments will be automatically expired after the length of it is complete, even across reboots.

	Should a temporary punishment expire whilst the bot is offline, the expiration will be automatically performed upon the next startup."""

	def __init__(self, bot):
		self.bot = bot

	async def error_handler(self, ctx, error, res):
		if isinstance(error, commands.CommandInvokeError):
			if isinstance(error.original, AlreadyMuted):
				await res("The user is already muted.")
				return True

			if isinstance(error.original, NotMuted):
				await res("The user hasn't been muted yet.")
				return True

			if isinstance(error.original, CannotPunish):
				await res(error.original.reason)
				return True

		return False

	def check_perms(self, actor, target):
		if isinstance(target, discord.User):
			return

		if actor == target:
			raise CannotPunish("You can't use that command on yourself")

		if target == actor.guild.owner:
			raise CannotPunish("The command doesn't work on the server owner")

		if target.top_role >= actor.top_role and actor != actor.guild.owner:
			raise CannotPunish(f"Your highest role ({actor.top_role}) must be above {target}'s highest role ({target.top_role})")

		if target.top_role >= actor.guild.me.top_role:
			raise CannotPunish(f"My highest role ({actor.guild.me.top_role.mention}) needs to be above {target}'s highest role ({target.top_role.mention})")

	@access_control.require(access_control.Level.MOD)
	@commands.command("bean",
		usage="bean <target:user> [reason:text]",
		hidden=True
	)
	@commands.bot_has_permissions(ban_members=True)
	async def bean(self, ctx, 
		target: discord.Member, 
		*, reason: str = "No reason given."
	):
		"""A little easter egg that allows you to pretend to ban a user."""

		self.check_perms(ctx.author, target)
		await ctx.success(f"{target} (`{target.id}`) has been beaned for:\n{reason}")

	@access_control.require(access_control.Level.MOD)
	@commands.command("ban",
		usage="ban <target:user> [reason:text]"
	)
	@commands.bot_has_permissions(ban_members=True)
	async def ban(self, ctx, 
		target: BanCandidateConverter, 
		*, reason: str = "No reason given."
	):
		"""Banishes a user from the server. Providing an ID allows for a hackban instead."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).ban(ctx.author, target, reason)
		await ctx.success(f"{target} (`{target.id}`) has been banned for:\n{reason}")

	@access_control.require(access_control.Level.MOD)
	@commands.command("tempban",
		usage="tempban <target:user> <duration:text> [reason:text]"
	)
	@commands.bot_has_permissions(ban_members=True)
	async def tempban(self, ctx, 
		target: BanCandidateConverter, 
		duration: DurationConverter, 
		*, reason: str = "No reason given."
	):
		"""Bans a user for a certain amount of time then unbans them afterwards."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).ban(ctx.author, target, reason, duration)
		await ctx.success(f"{target} (`{target.id}`) has been banned for {time_since(seconds=duration)} for:\n{reason}")

	@access_control.require(access_control.Level.MOD)
	@commands.command("unban",
		usage="unban <target:user>"
	)
	@commands.bot_has_permissions(ban_members=True)
	async def unban(self, ctx,
		target: BanCandidateConverter
	):
		"""Removes a ban placed on a provided user."""

		await Handler(self.bot, ctx.guild).unban(ctx.author, target)
		await ctx.success(f"{target} (`{target.id}`) has been unbanned.")

	@access_control.require(access_control.Level.MOD)
	@commands.command("kick",
		usage="kick <target:user> [reason:text]"
	)
	@commands.bot_has_permissions(kick_members=True)
	async def kick(self, ctx,
		target: discord.Member,
		*, reason: str = "No reason given."
	):
		"""Kicks a user from the server."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).kick(ctx.author, target, reason)
		await ctx.success(f"{target} (`{target.id}`) has been kicked for:\n{reason}")

	@access_control.require(access_control.Level.MOD)
	@commands.command("mute",
		usage="mute <target:user> [reason:text]"
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def mute(self, ctx,
		target: discord.Member,
		*, reason: str = "No reason given."
	):
		"""Gives the provided user the configured mute role."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).mute(ctx.author, target, reason)
		await ctx.success(f"{target} (`{target.id}`) has been muted for:\n{reason}")

	@access_control.require(access_control.Level.MOD)
	@commands.command("tempmute",
		usage="tempmute <target:user> <duration:text> [reason:text]"
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def tempmute(self, ctx,
		target: discord.Member,
		duration: DurationConverter,
		*, reason: str = "No reason given."
	):
		"""Temporarily adds the mute role to a user then removes it after."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).mute(ctx.author, target, reason, duration)
		await ctx.success(f"{target} (`{target.id}`) has been muted for {time_since(seconds=duration)} for:\n{reason}")

	@access_control.require(access_control.Level.MOD)
	@commands.command("unmute",
		usage="unmute <target:user>"
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def unmute(self, ctx,
		target: discord.Member
	):
		"""Removes the configured mute role from the user."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).unmute(ctx.author, target)
		await ctx.success(f"{target} (`{target.id}`) has been unmuted.")

	@access_control.require(access_control.Level.MOD)
	@commands.command("warn",
		usage="warn <target:user> <reason:text>"
	)
	async def warn(self, ctx,
		target: discord.Member,
		*, reason: str
	):
		"""Issues a logged warning to the provided user."""

		self.check_perms(ctx.author, target)
		await Handler(self.bot, ctx.guild).warn(ctx.author, target, reason)
		await ctx.success(f"{target} (`{target.id}`) has been warned for:\n{reason}")

	@commands.group("inf",
		usage="inf",
		aliases=["infractions"],
		invoke_without_command=True
	)
	async def inf(self, ctx):
		"""This allows you to see and delete infractions."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.ADMIN)
	@inf.command("clear",
		usage="inf clear <target:user|num>"
	)
	async def inf_clear(self, ctx,
		target: Union[BanCandidateConverter, int]
	):
		"""Admins can wipe a user's infractions or delete a specific one with this command."""

		async with self.bot.postgres.acquire() as con:
			if isinstance(target, (discord.Member, discord.User)):
				search_id = target.id
				query = """DELETE FROM infractions WHERE target_id = $1 AND guild_id = $2 RETURNING *;"""

			else:
				search_id = target
				query = """DELETE FROM infractions WHERE id = $1 AND guild_id = $2 RETURNING *;"""

			cases = await con.fetch(query, search_id, ctx.guild.id)

			if not cases:
				raise LookupFailed("infractions")

			await ctx.success(f"{len(cases)} infractions have been cleared.")

	@access_control.require(access_control.Level.MOD)
	@inf.command("search",
		usage="inf search <target:user|num>"
	)
	async def inf_search(self, ctx,
		target: Union[BanCandidateConverter, int]
	):
		"""Fetches a specific infraction with the provided ID or lists a user's infractions."""

		MAX = 10
		TS_FORMAT = "%d/%m/%y %H:%M:%S"

		async with self.bot.postgres.acquire() as con:
			if isinstance(target, (discord.Member, discord.User)):
				search_id = target.id
				query = """SELECT id, target_id, actor_id, type_id, reason, created_at FROM infractions
						   WHERE (target_id = $1 OR actor_id = $1) AND guild_id = $2
						   ORDER BY id DESC;"""

			else:
				search_id = target
				query = """SELECT id, target_id, actor_id, type_id, reason, created_at FROM infractions
						   WHERE id = $1 AND guild_id = $2;"""

			cases = await con.fetch(query, search_id, ctx.guild.id)

			if not cases:
				raise LookupFailed("infractions")

			type_str = {
				0: "ban",
				1: "kick",
				2: "mute",
				3: "warn"
			}

			await ctx.send(dedent(f"""🔎 Showing {len(cases[:MAX])}/{len(cases)} found infractions:
				```md
				{tabulate(
					tabular_data=[
						[
							infraction["id"],
							clean_user(ctx.guild, infraction["target_id"]),
							clean_user(ctx.guild, infraction["actor_id"]),
							type_str.get(infraction["type_id"]),
							infraction["reason"],
							infraction["created_at"].strftime(TS_FORMAT)
						] for infraction in cases[:MAX]
					],
					headers=("ID", "Target", "Actor", "Type", "Reason", "Timestamp"),
					tablefmt="simple",
					numalign="left", 
					stralign="left"
				)}```"""))

	@access_control.require(access_control.Level.MOD)
	@inf.command("recent",
		usage="inf recent"
	)
	async def inf_recent(self, ctx):
		"""Shows the most recent infractions for the server."""

		MAX = 10
		TS_FORMAT = "%d/%m/%y %H:%M:%S"

		async with self.bot.postgres.acquire() as con:
			query = """SELECT id, target_id, actor_id, type_id, reason, created_at FROM infractions
					   WHERE guild_id = $1
					   ORDER BY created_at DESC;"""

			cases = await con.fetch(query, ctx.guild.id)
			if not cases:
				raise LookupFailed("infractions")

			type_str = {
				0: "ban",
				1: "kick",
				2: "mute",
				3: "warn"
			}

			await ctx.send(dedent(f"""🔎 Showing {len(cases[:MAX])}/{len(cases)} found infractions:
				```md
				{tabulate(
					tabular_data=[
						[
							infraction["id"],
							clean_user(ctx.guild, infraction["target_id"]),
							clean_user(ctx.guild, infraction["actor_id"]),
							type_str.get(infraction["type_id"]),
							infraction["reason"],
							infraction["created_at"].strftime(TS_FORMAT)
						] for infraction in cases[:MAX]
					],
					headers=("ID", "Target", "Actor", "Type", "Reason", "Timestamp"),
					tablefmt="simple",
					numalign="left", 
					stralign="left"
				)}```"""))

	@commands.Cog.listener()
	async def on_temp_mute_expire(self, target_id, guild_id, case_id):
		guild = self.bot.get_guild(guild_id)
		target = guild.get_member(target_id)
		config = Handler(self.bot, guild)

		if not guild.me.guild_permissions.manage_roles or config.mute_role is None:
			return

		if target is not None:
			if config.mute_role not in target.roles:
				return

			await config.unmute(guild.me, target, case_id)

		else:
			async with self.bot.postgres.acquire() as con:
				query = """SELECT role_ids FROM persistent_roles
						   WHERE user_id = $1 AND guild_id = $2;"""

				persistent_roles = await con.fetchval(query, target.id, guild.id)

				if persistent_roles:
					roles_as_list = literal_eval(persistent_roles)
					roles_as_list.remove(config.mute_role.id)

					query = """UPDATE persistent_roles SET role_ids = $1
							   WHERE user_id = $2 AND guild_id = $3;"""

					await con.execute(query, str(roles_as_list), target.id, guild.id)

	@commands.Cog.listener()
	async def on_temp_ban_expire(self, target_id, guild_id, case_id):
		guild = self.bot.get_guild(guild_id)

		if not guild.me.guild_permissions.ban_members:
			return

		target = await self.bot.fetch_user(target_id)
		if target is None:
			return

		try:
			await Handler(self.bot, guild).unban(guild.me, target, case_id)

		except:
			pass

	@commands.Cog.listener()
	async def on_member_unban(self, guild, user):
		expiring_timer = state.timer_handler.get("temp_ban", {
				"target_id": user.id,
				"guild_id": guild.id
			}
		)

		if expiring_timer is not None:
			await expiring_timer.cancel()

	@commands.Cog.listener("on_member_update")
	async def on_premature_unmute(self, before, after):
		config = Handler(self.bot, after.guild)

		if before.roles == after.roles or config.mute_role is None:
			return

		if config.mute_role not in after.roles and config.mute_role in before.roles:
			expiring_timer = state.timer_handler.get("temp_mute", {
					"target": after.id,
					"guild": after.guild.id
				}
			)

			if expiring_timer is not None:
				await expiring_timer.cancel()


def setup(bot):
	cog = Plugin(bot)
	bot.add_cog(cog)
	bot.dispatch("cog_load", cog)