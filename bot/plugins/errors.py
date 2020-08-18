import discord

import core.prefix as prefix

from discord.ext import commands
from traceback import format_tb

from ext.exceptions import AccessDenied, LookupFailed, MissingSubcommand, NotConfigured
from ext.utils import time_since


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self._handlers = [self.basic_handler]

	async def make_embed(self, ctx):
		details = f"```{prefix.default}{ctx.command.usage}```\n"

		if ctx.command.aliases:
			details += f"**Can also use:** {', '.join(f'`{alias}`' if not ctx.command.full_parent_name else f'`{ctx.command.full_parent_name} {alias}`' for alias in ctx.command.aliases)}\n"

		if not await ctx.command.can_run(ctx):
			details += "***You cannot run this command.***\n"

		details += f"*{ctx.command.short_doc or 'No description available.'}*\n"

		if isinstance(ctx.command, commands.Group):
			if len(ctx.command.commands) > 0:
				details += "\n**Subcommands:**\n\n" + "\n".join(f"**`{command.usage}`**\n*{command.short_doc or 'No description available.'}*" for command in ctx.command.commands)

		embed = discord.Embed(
			description=details
		)
		embed.set_author(
			name="Command Help"
		)

		return embed

	async def basic_handler(self, ctx, error, res):
		IGNORED = (
			commands.CommandNotFound,
			commands.NoPrivateMessage,
			commands.DisabledCommand
		)

		if isinstance(error, IGNORED):
			return True
		
		if isinstance(error, commands.MissingRequiredArgument):
			await res(f"You're missing a required argument: `{error.param}`", True)
			return True

		if isinstance(error, (commands.BadArgument, commands.BadUnionArgument)):
			await res(f"You provided an incorrect argument: `{list(ctx.command.clean_params)[len(ctx.args[2:] if ctx.command.cog else ctx.args[1:])]}`", True)
			return True

		if isinstance(error, commands.CommandOnCooldown):
			await res(f"This command is on cooldown, try again after **{time_since(seconds=error.retry_after)}**.")
			return True

		if isinstance(error, commands.BotMissingPermissions):
			await res(f"I'm missing some permissions required to perform this action: `{', '.join(error.missing_perms)}`.")
			return True

		if isinstance(error, (commands.CheckFailure, commands.CheckAnyFailure)):
			await res("You're not allowed to use that command.")
			return True

		if isinstance(error, commands.CommandInvokeError):
			if isinstance(error.original, MissingSubcommand):
				await res("You're missing a subcommand.", True)
				return True

			if isinstance(error.original, LookupFailed):
				await res(f"No {error.original.item} were found with your query.")
				return True

			if isinstance(error.original, NotConfigured):
				await res(f"A required setting is missing from the server config: `{error.original.missing_config}`.")
				return True

			if isinstance(error.original, AccessDenied):
				await res("You're not allowed to use that command.")
				return True

		return False

	@commands.Cog.listener()
	async def on_cog_load(self, cog):
		if not hasattr(cog, "error_handler"):
			return

		self._handlers.append(cog.error_handler)

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		async def response(content, help_embed=False, **kwargs):
			FORMAT = "{emoji} | {ctx.author.mention}: {content}"

			if help_embed:
				embed = await self.make_embed(ctx)

			else:
				embed = None

			try:
				return await ctx.send(FORMAT.format(
					emoji=self.bot.emojis.get("cross", "🚫"),
					ctx=ctx,
					content=content
				), 
					embed=embed,
					**kwargs
				)

			except discord.HTTPException:
				pass

		for handler in self._handlers:
			if await handler(ctx, error, response):
				return

		await response("Unknown error, check the logs.")
		traceback = "\n".join(format_tb(error.original.__traceback__))
		self.bot.log.error(f"Untracked error occured in {ctx.command}:\n{traceback}\n{error}")


def setup(bot):
	bot.add_cog(Plugin(bot))