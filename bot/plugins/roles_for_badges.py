import discord

from discord.ext import commands

from ext.exceptions import CustomException, MissingSubcommand
from ext.state import access_control
from ext.utils import first


class CannotSync(CustomException):
	def __init__(self, reason):
		self.reason = reason

class FlagEnum:
	STAFF            = 1
	PARTNER          = 2
	HS_EVENTS        = 4
	BUG_HUNTER_1     = 8
	HS_BRAVERY       = 64
	HS_BRILLIANCE    = 128
	HS_BALANCE       = 256
	EARLY_SUPPORTER  = 512
	BUG_HUNTER_2     = 16384
	VERIFIED_BOT_DEV = 131072


class Flag:
	def __init__(self, guild, flag, role):
		self.flag = flag
		self.role = guild.get_role(role)

class Config:
	def __init__(self, bot, guild, config):
		self.bot = bot

		raw = config.get("roles_for_badges", {})

		self.enabled = raw.get("enabled", False)
		self.sync_on = raw.get("sync_on", [])
		self.flags = [Flag(guild, f, r) for f, r in raw.get("flags", {}).items()]

	@classmethod
	async def new(cls, bot, guild):
		config = await bot.get_config(guild)
		return cls(bot, guild, config)

	async def sync(self, member, flag_override=None):
		ALL_FLAGS = [1, 2, 4, 8, 64, 128, 256, 512, 16384, 131072]
		
		if flag_override is None:
			member_flags = [f.value for f in member.public_flags.all()]
		
		else:
			member_flags = flag_override
		
		assign = []
		remove = []

		for flag in ALL_FLAGS:
			config = self.get(flag)
			if config is None:
				continue

			if flag in member_flags and config.role not in member.roles:
				assign.append(config.role)
			
			elif flag not in member_flags and config.role in member.roles:
				remove.append(config.role)

		await member.add_roles(*assign)
		self.bot.log.debug(f"Roles for badges: assigned {len(assign)} roles to {member} in {member.guild}.")

		await member.remove_roles(*remove)
		self.bot.log.debug(f"Roles for badges: removed {len(remove)} roles from {member} in {member.guild}.")

		return len(assign), len(remove)

	def get(self, flag):
		return first(self.flags, lambda f: f.flag == flag)

	@property
	def staff(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.STAFF)
	
	@property
	def partner(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.PARTNER)

	@property
	def events(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.HS_EVENTS)

	@property
	def hunter(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.BUG_HUNTER_1)

	@property
	def bravery(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.HS_BRAVERY)

	@property
	def brilliance(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.HS_BRILLIANCE)

	@property
	def balance(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.HS_BALANCE)

	@property
	def early_supporter(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.EARLY_SUPPORTER)

	@property
	def gold_hunter(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.BUG_HUNTER_2)

	@property
	def verified_dev(self):
		return first(self.flags, lambda f: f.flag == FlagEnum.VERIFIED_BOT_DEV)


class Plugin(commands.Cog, name="Roles for Badges"):
	"""Roles for Badges (shortened to rfb) allows Captain to automatically assign roles to users depending on what profile badges they have.
	
	This is especially useful when you want to give special roles to users with special badges. For example, a Discord Partner should have a special role to recognise their importance."""

	def __init__(self, bot):
		self.bot = bot

	async def error_handler(self, ctx, error, res):
		if isinstance(error, commands.CommandInvokeError):
			if isinstance(error.original, CannotSync):
				await res(error.original.reason)
				return True

		return False

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if member.bot:
			return

		config = await Config.new(self.bot, member.guild)
		if config.enabled and "JOIN" in config.sync_on:
			await config.sync(member)

	@access_control.require(access_control.Level.DEFAULT)
	@commands.group("rfb",
		usage="rfb",
		aliases=["rolesforbadges", "badges"],
		invoke_without_command=True
	)
	async def rfb(self, ctx):
		"""An interface to interact with roles for badges."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.DEFAULT)
	@rfb.group("sync",
		usage="rfb sync",
		invoke_without_command=True
	)
	async def rfb_sync(self, ctx):
		"""Allows for synchronisation of rfb."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.DEFAULT)
	@rfb_sync.command("me",
		usage="rfb sync me"
	)
	@commands.cooldown(1, 3600, commands.BucketType.user)
	async def rfb_sync_me(self, ctx):
		"""Sychronises rfb for yourself."""

		async with ctx.channel.typing():
			fetched_user = await self.bot.fetch_user(ctx.author.id)
			fetched_flags = [f.value for f in fetched_user.public_flags.all()]

			config = await Config.new(self.bot, ctx.guild)
			assigned, removed = await config.sync(ctx.author, fetched_flags)

			if not assigned and not removed:
				return await ctx.success("You're all caught up, no need to synchronise your roles!")

			await ctx.success(f"You were given {assigned} roles and lost {removed} roles!")

	@access_control.require(access_control.Level.MOD)
	@rfb_sync.command("user",
		usage="rfb sync user <target:user>"
	)
	async def rfb_sync_user(self, ctx,
		target: discord.Member
	):
		"""Allows Moderators to synchronise rfb for a specific user."""

		if target.bot:
			raise CannotSync("Cannot sync rfb for bot accounts.")

		async with ctx.channel.typing():
			fetched_user = await self.bot.fetch_user(target.id)
			fetched_flags = [f.value for f in fetched_user.public_flags.all()]

			config = await Config.new(self.bot, ctx.guild)
			assigned, removed = await config.sync(target, fetched_flags)

			if not assigned and not removed:
				return await ctx.success(f"{target} is all caught up, no need to synchronise their roles!")

			await ctx.success(f"{target} was given {assigned} roles and lost {removed} roles!")


def setup(bot):
	cog = Plugin(bot)
	bot.add_cog(cog)
	bot.dispatch("cog_load", cog)