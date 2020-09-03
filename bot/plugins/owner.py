import discord

from discord.ext import commands
from yaml import safe_load

from ext.exceptions import MissingSubcommand


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def cog_check(self, ctx):
		return await self.bot.is_owner(ctx.author)

	@commands.group("control",
		usage="control",
		invoke_without_command=True
	)
	async def control(self, ctx):
		"""Allows bot owners to control the bot from Discord."""

		raise MissingSubcommand()

	@control.command("shutdown",
		usage="control shutdown",
		aliases=["kill", "close", "quit", "exit"]
	)
	async def control_shutdown(self, ctx):
		"""Gracefully shuts down."""

		await ctx.success("Shutting down, later taters!")
		await self.bot.shutdown()

	@control.group("reload",
		usage="reload",
		invoke_without_command=True
	)
	async def control_reload(self, ctx):
		"""Allows bot owners to reload certain config files."""

		raise MissingSubcommand()

	@control_reload.command("guilds",
		usage="guilds"
	)
	async def control_reload_guilds(self, ctx):
		"""Reloads the guilds.yml file containing guild configurations."""

		self.bot.configs = safe_load(open("guilds.yml"))
		await ctx.success("The `guilds.yml` file has been reloaded!")


def setup(bot):
	bot.add_cog(Plugin(bot))