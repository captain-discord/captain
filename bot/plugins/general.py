import discord, os.path

from discord.ext import commands
from inspect import getsourcelines
from time import perf_counter

from ext.exceptions import LookupFailed
from ext.state import access_control


class Plugin(commands.Cog, name="Utility Commands"):
	"""These commands provide simple utility functions like sending a link to the source of a specific command or fetching the bot's ping."""

	def __init__(self, bot):
		self.bot = bot 

	@access_control.require(access_control.Level.DEFAULT)
	@commands.command("ping",
		usage="ping"
	)
	async def ping(self, ctx):
		"""Shows you how long it takes for the bot to send/receive messages."""

		start = perf_counter()
		message = await ctx.send("⏱️ Fetching connection latency...")
		stop = perf_counter()

		await message.edit(content=f"🏓 **Roundtrip:** {round((stop - start) * 1000)} ms | **Websocket:** {round(ctx.bot.latency * 1000)} ms")

	@access_control.require(access_control.Level.DEFAULT)
	@commands.command("source",
		usage="source [command:text]"
	)
	async def source(self, ctx, 
		*, command: str = None
	):
		"""Provides a link to the source code of the provided command."""

		BASE = "https://github.com/Jack-Gledhill/captain"
		BRANCH = "master"

		if command is None:
			return await ctx.send(f"🔧 Source for the full bot:\n<{BASE}>")

		cmd_obj = self.bot.get_command(command.replace(".", " "))
		
		if cmd_obj is None:
			raise LookupFailed("commands")
		
		src = cmd_obj.callback.__code__
		lines, firstlineno = getsourcelines(src)
		location = os.path.relpath(src.co_filename).replace("\\", "/")

		await ctx.send(f"🔧 Source for {cmd_obj.name} command:\n<{BASE}/blob/{BRANCH}/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>")


def setup(bot):
	cog = Plugin(bot)
	bot.add_cog(cog)
	bot.dispatch("cog_load", cog)