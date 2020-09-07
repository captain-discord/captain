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
	def __init__(self, guild, config):
		self.levels = [Level(guild, r, **options) for r, options in config.get("access_control", {}).items()]

	@classmethod
	async def new(cls, bot, guild):
		config = await bot.get_config(guild)
		return cls(guild, config)

	def can_use(self, member, command, needed_level):
		if member.guild_permissions.administrator:
			return True

		all_levels = [l for l in self.levels if l.role in member.roles]

		if not all_levels:
			return False

		top_level = sorted(all_levels,
			key=lambda i: i.level
		)[0]
		
		overwrites = [(l.overwrites.get(command.qualified_name), l.level) for l in all_levels]

		if overwrites:
			overwritten = list(filter(None.__ne__, [i[0] for i in sorted(overwrites,
				key=lambda i: i[1]
			)]))

		else:
			overwritten = None

		if overwritten:
			return overwritten[0]

		return top_level.level >= needed_level

class Plugin(commands.Cog):
	class Level:
		DEFAULT = 0
		TRUSTED = 10
		MOD     = 90
		ADMIN   = 100


	def __init__(self, bot):
		self.bot = bot

	def require(self, level):
		async def predicate(ctx):
			config = await Config.new(self.bot, ctx.guild)
			return config.can_use(ctx.author, ctx.command, level)

		return commands.check(predicate)


def setup(bot):
	ext.state.access_control = cog = Plugin(bot)

	bot.add_cog(cog)