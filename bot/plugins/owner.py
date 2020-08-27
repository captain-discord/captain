import discord

from discord.ext import commands
from yaml import safe_load

from ext.exceptions import MissingSubcommand


class Plugin(commands.Cog, command_attrs={"hidden": True}):
	def __init__(self, bot):
		self.bot = bot

	async def cog_check(self, ctx):
		return await self.bot.is_owner(ctx.author)

	@commands.group("reload",
		usage="reload",
		invoke_without_command=True
	)
	async def reload(self, ctx):
		"""Allows bot owners to reload certain config files."""

		raise MissingSubcommand()

	@reload.command("guilds",
		usage="guilds"
	)
	async def reload_guilds(self, ctx):
		"""Reloads the guilds.yml file containing guild configurations."""

		self.bot.guilds = safe_load(open("guilds.yml"))
		await ctx.success("The `guilds.yml` file has been reloaded!")


def setup(bot):
	bot.add_cog(Plugin(bot))