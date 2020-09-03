import discord, os

from claptcha import Claptcha
from datetime import datetime
from discord.ext import commands
from PIL import Image
from random import choice
from string import ascii_letters

from ext.exceptions import CustomException, MissingSubcommand, NotConfigured, NotEnabled
from ext.state import access_control
from ext.utils import fmt_prefix


class ActionEnum:
	ADD_ROLE    = 0
	REMOVE_ROLE = 1

class TypeEnum:
	AGREE_CMD = 0
	CAPTCHA   = 1


class AlreadyVerified(CustomException):
	pass


class GatekeeperManifest:
	def __init__(self, member, guild, **performed_checks):
		self.member = member
		self.guild = guild

		self.avatar_check = performed_checks.pop("avatar_check", False)
		self.age_check = performed_checks.pop("age_check", False)

		self.checks = self.avatar_check, self.age_check

	@property
	def successful(self):
		return len([c for c in self.checks if c is True])

	@property
	def failed(self):
		return len([c for c in self.checks if c is False])

	@property
	def undetermined(self):
		return len([c for c in self.checks if c is None])

class Config:
	def __init__(self, bot, guild):
		self.bot = bot
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.configs.get(self.guild.id, {}).get("gatekeeper", {})

		self.enabled = self.raw.get("enabled", False)

		self.min_age = self.raw.get("min_age", 604800)
		self.checks_for_bypass = self.raw.get("checks_for_bypass", 2)

		self.action = self.raw.get("action", 0)
		self.type = self.raw.get("type", 0)
		self.role = guild.get_role(self.raw.get("role"))

		self.extras = self.raw.get("extras", {})

		self._captcha_locks = set()

	async def verify(self, member):
		if self.action == ActionEnum.ADD_ROLE:
			await member.add_roles(self.role)

		else:
			await member.remove_roles(self.role)

	def gen_captcha(self):
		text = "".join(choice(ascii_letters) for _ in range(self.extras.get("char_length", 6)))
		filename = "".join(choice(ascii_letters) for _ in range(12)) + ".png"
		
		c = Claptcha(text, choice([f"fonts/{f}" for f in os.listdir("fonts")]),
			resample=Image.BICUBIC,
			noise=self.extras.get("noise", 0.3)
		)
		c.write(filename)

		return text, filename

	async def handle_captcha(self, ctx):
		if ctx.author.id in self._captcha_locks:
			return await ctx.failure("You already have a captcha check running in your DMs, finish it then try again!")

		self._captcha_locks.add(ctx.author.id)

		looking_for, path = self.gen_captcha()
		attempts = self.extras.get("attempts", 3)

		embed = discord.Embed(
			colour=0x7289DA,
			title="Verification Required",
			description=f"Hey {ctx.author.name},\n\nTo gain access to {ctx.guild}, you'll first need to complete the captcha below. You have {attempts} attempts before you have to generate a new one so don't worry if you make a typo!\n\nTo complete the captcha, simply type out the correct letters (case sensitive) and send them here as DMs!"
		)
		embed.set_image(url=f"attachment://image.png")

		try:
			# d.py has a very strange way of handling local files in embed images
			await ctx.author.send(
				file=discord.File(path, 
					filename="image.png"
				), 
				embed=embed
			)

		except discord.Forbidden:
			self._captcha_locks.remove(ctx.author.id)
			return await ctx.failure("I tried to DM you but it failed. Please check your DM settings and try again!")

		os.remove(path)

		for i in range(attempts):
			msg = await self.bot.wait_for("message",
				check=lambda m: isinstance(m.channel, discord.DMChannel) and m.author == ctx.author
			)

			if msg.content == looking_for:
				await self.verify(ctx.author)
				self._captcha_locks.remove(ctx.author.id)
				return await ctx.author.send(f"{self.bot.emojis.get('tick', '✅')} | Correct! You've been given access to {ctx.guild}.")

			elif i + 1 != attempts:
				await ctx.author.send(f"{self.bot.emojis.get('cross', '❌')} | That's incorrect, you have {attempts - (i + 1)} attempts left.")

		await ctx.author.send(f"{self.bot.emojis.get('cross', '❌')} | That's incorrect! To try again, run `{fmt_prefix('verify me')}` in {ctx.channel.mention}.")
		self._captcha_locks.remove(ctx.author.id)

	def run_checks(self, member):
		avatar_check = False
		if member.avatar is not None:
			avatar_check = True

		age_check = False
		if (datetime.utcnow() - member.created_at).total_seconds() >= self.min_age:
			age_check = True

		return GatekeeperManifest(member, member.guild, 
			avatar_check=avatar_check,
			age_check=age_check
		)


class Plugin(commands.Cog, name="User Verification"):
	def __init__(self, bot):
		self.bot = bot

	async def error_handler(self, ctx, error, res):
		if isinstance(error, commands.CommandInvokeError):
			if isinstance(error.original, AlreadyVerified):
				await res("The target is already verified.")
				return True

		return False

	@commands.group("verify",
		usage="verify",
		invoke_without_command=True
	)
	async def verify(self, ctx):
		"""Allows users to verify themselves."""

		raise MissingSubcommand()

	@verify.command("me",
		usage="verify me"
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def verify_me(self, ctx):
		"""Activates gatekeeper for yourself."""

		config = Config(self.bot, ctx.guild)

		if config.role is None:
			raise NotConfigured("gatekeeper.role")

		if not config.enabled:
			raise NotEnabled("gatekeeper")

		if config.type == TypeEnum.AGREE_CMD:
			await config.verify(ctx.author)

		elif config.type == TypeEnum.CAPTCHA:
			await config.handle_captcha(ctx)

	@access_control.require(access_control.Level.MOD)
	@verify.command("user",
		usage="verify user <target:user>"
	)
	@commands.bot_has_permissions(manage_roles=True)
	async def verify_user(self, ctx,
		target: discord.Member
	):
		"""Bypasses gatekeeper for a specific user."""

		config = Config(self.bot, ctx.guild)
		if config.role is None:
			raise NotConfigured("gatekeeper.role")

		if not config.enabled:
			raise NotEnabled("gatekeeper")

		if (config.role in target.roles and config.action == ActionEnum.ADD_ROLE) \
			or (config.role not in target.roles and config.action == ActionEnum.REMOVE_ROLE):
			raise AlreadyVerified()

		await config.verify(target)
		await ctx.success(f"{target} has been verified.")

	@commands.Cog.listener()
	async def on_member_join(self, member):
		config = Config(self.bot, member.guild)
		if not config.enabled or config.role is None or not member.guild.me.guild_permissions.manage_roles or member.bot:
			return

		manifest = config.run_checks(member)

		if isinstance(config.checks_for_bypass, int):
			if config.checks_for_bypass <= manifest.successful:
				if config.action == ActionEnum.ADD_ROLE:
					return await member.add_roles(config.role)

				elif config.action == ActionEnum.REMOVE_ROLE:
					return

		if config.action == ActionEnum.ADD_ROLE:
			return

		await member.add_roles(config.role)


def setup(bot):
	cog = Plugin(bot)
	bot.add_cog(cog)
	bot.dispatch("cog_load", cog)