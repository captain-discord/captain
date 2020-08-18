import discord

from discord.ext import commands

from ext.converters import BanCandidateConverter
from ext.exceptions import MissingSubcommand
from ext.state import access_control


class Plugin(commands.Cog):
	HELP_MANIFEST = {
		"name": "Purging Messages",
		"description": """
		The purge commands (aka nuke and clean commands) allow Moderators to delete a large number of messages at once with relative ease.

		There is a large variety of subcommands here that allow for more verbosity when telling the bot which messages to delete. E.g. using `purge bots` will only delete messages that were sent by bot accounts.
		"""
	}

	def __init__(self, bot):
		self.bot = bot

	@commands.group("purge",
		usage="purge",
		aliases=["clean", "nuke"],
		invoke_without_command=True
	)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge(self, ctx):
		"""Allows Moderators to delete a large number of messages at once."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.MOD)
	@purge.command("here",
		usage="purge here <amount:num>"
	)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_here(self, ctx, 
		amount: int
	):
		"""Deletes a large number of messages from the current channel."""

		await ctx.message.delete()
		purged = await ctx.channel.purge(limit=amount)
		
		await ctx.success(f"{len(purged)} messages have been purged.",
			delete_after=15
		)

	@access_control.require(access_control.Level.MOD)
	@purge.command("user",
		usage="purge user <amount:num> <target:user>"
	)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_user(self, ctx,
		amount: int,
		target: BanCandidateConverter
	):
		"""Purges messages sent by the provided user."""

		await ctx.message.delete()
		purged = await ctx.channel.purge(
			limit=amount,
			check=lambda m: m.author.id == target.id
		)
		
		await ctx.success(f"{len(purged)} messages by {target} have been purged.",
			delete_after=15
		)

	@access_control.require(access_control.Level.MOD)
	@purge.command("channel",
		usage="purge channel <amount:num> <target:channel>"
	)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_channel(self, ctx,
		amount: int,
		target: discord.TextChannel
	):
		"""Allows Moderators to purge a large number of messages from the provided channel."""

		await ctx.message.delete()
		purged = await target.purge(limit=amount)
		
		await ctx.success(f"{len(purged)} messages in {target.mention} have been purged.",
			delete_after=15
		)

	@access_control.require(access_control.Level.MOD)
	@purge.command("bots",
		usage="purge bots <amount:num> [target:channel]"
	)
	@commands.bot_has_permissions(manage_messages=True)
	async def purge_bots(self, ctx,
		amount: int,
		target: discord.TextChannel = None
	):
		"""Purges messages only sent by bots with an optional channel."""

		target = target or ctx.channel

		await ctx.message.delete()
		purged = await target.purge(
			limit=amount,
			check=lambda m: m.author.bot
		)

		await ctx.success(f"{len(purged)} messages in {target.mention} by bot accounts have been purged.",
			delete_after=15
		)


def setup(bot):
	bot.add_cog(Plugin(bot))