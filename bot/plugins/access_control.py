import discord

import ext.state

from discord.ext import commands

from ext.utils import first


class Level:
	def __init__(self, guild, id, **options):
		self.role = guild.get_role(id) if id not in ("@everyone", "everyone") else guild.default_role

		self.level = options.get("level", 0)
		self.overwrites = options.get("overwrites", {})

class Config:
	def __init__(self, bot, guild):
		self.bot = bot
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id, {}).get("access_control", {})
		self.levels = [Level(self.guild, r, **options) for r, options in self.raw.items()]

	def can_use(self, member, command, needed_level):
		if member.guild_permissions.administrator:
			return True

		all_levels = [l for l in self.levels if l.role in member.roles]

		if not all_levels:
			return False

		top_level = sorted(all_levels,
			key=lambda i: i.level
		)[0]
		
		overwrites = list(filter(None, [(l.overwrites.get(command.qualified_name), l.level) for l in all_levels]))

		if overwrites:
			overwritten = sorted(overwrites,
				key=lambda i: i[1]
			)

		else:
			overwritten = None

		if overwritten is not None:
			return overwritten

		return top_level.level >= needed_level

class Plugin(commands.Cog):
	class Level:
		DEFAULT = 0
		TRUSTED = 10
		MOD     = 90
		ADMIN   = 100


	def __init__(self, bot):
		self.bot = bot

		self.bot.add_check(self.require_default_level)

	async def require_default_level(self, ctx):
		return Config(self.bot, ctx.guild).can_use(ctx.author, ctx.command, self.Level.DEFAULT)

	def require(self, level):
		async def predicate(ctx):
			return Config(self.bot, ctx.guild).can_use(ctx.author, ctx.command, level)

		return commands.check(predicate)


def setup(bot):
	ext.state.access_control = cog = Plugin(bot)

	bot.add_cog(cog)