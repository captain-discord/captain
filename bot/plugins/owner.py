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


def setup(bot):
	bot.add_cog(Plugin(bot))