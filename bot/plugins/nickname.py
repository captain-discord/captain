import discord

from discord.ext import commands, tasks

from ext.exceptions import CustomException, MissingSubcommand
from ext.state import access_control


class CannotNick(CustomException):
	def __init__(self, reason):
		self.reason = reason

class NickTooLong(CustomException):
	pass

class NickNotSet(CustomException):
	pass

class Plugin(commands.Cog, name="Nickname Commands"):
	"""These commands make it easier for Moderators to add, edit and remove a user's nickname."""
	
	def __init__(self, bot):
		self.bot = bot

		self.nickname_updater.start()

	async def error_handler(self, ctx, error, res):
		if isinstance(error, commands.CommandInvokeError):
			if isinstance(error.original, NickNotSet):
				await res("The user doesn't have a nickname.")
				return True

			if isinstance(error.original, NickTooLong):
				await res("The provided nickname is too long to set.")
				return True
			
			if isinstance(error.original, CannotNick):
				await res(error.original.reason)
				return True

		return False

	@tasks.loop(seconds=300)
	async def nickname_updater(self):
		for guild in self.bot.guilds:
			config = await self.bot.get_config(guild)
			nick = config.get("nickname")
			
			if guild.me.guild_permissions.change_nickname:
				await guild.me.edit(nick=nick)
				self.bot.log.debug(f"Updated nickname for {guild.id}.")

	@nickname_updater.before_loop
	async def nickname_updater_wait(self):
		await self.bot.wait_until_ready()

	def check_perms(self, actor, target):
		if target == actor.guild.owner:
			raise CannotNick("You can't change the nickname of the server owner.")

		if target.top_role.position >= actor.top_role.position and actor != actor.guild.owner:
			raise CannotNick(f"Your highest role ({actor.top_role}) must be above {target}'s highest role ({target.top_role})")

	@access_control.require(access_control.Level.MOD)
	@commands.group("nickname",
		usage="nickname",
		aliases=["nick"],
		invoke_without_command=True
	)
	async def nickname(self, ctx):
		"""Allows Mods to add, change or remove a user's nickname"""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.MOD)
	@nickname.command("add",
		usage="nickname add <target:user> <nickname:text>",
		aliases=["new", "create", "set", "update", "change"],
	)
	async def nickname_add(self, ctx,
		target: discord.Member,
		*, nick: str
	):
		"""Adds or updates a user's nickname."""

		MAX_LENGTH = 32

		self.check_perms(ctx.author, target)
		if len(nick) > MAX_LENGTH:
			raise NickTooLong()

		await target.edit(nick=nick)
		await ctx.success(f"{target}'s nickname has been set to: `{nick}`.")

	@access_control.require(access_control.Level.MOD)
	@nickname.command("remove",
		usage="nickname remove <target:user>",
		aliases=["delete", "reset"]
	)
	async def nickname_remove(self, ctx,
		target: discord.Member
	):
		"""Removes a user's nickname."""

		self.check_perms(ctx.author, target)
		if target.nick is None:
			raise NickNotSet()

		await target.edit(nick=None)
		await ctx.success(f"{target}'s nickname has been removed.")


def setup(bot):
	cog = Plugin(bot)
	bot.add_cog(cog)
	bot.dispatch("cog_load", cog)