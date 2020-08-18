import discord

from discord.ext import commands


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

		self.bot.add_check(self.is_configured)
		self.bot.add_check(self.can_speak)
		self.bot.add_check(self.response_injector)

	def cog_unload(self):
		self.bot.remove_check(self.is_configured)
		self.bot.remove_check(self.can_speak)
		self.bot.remove_check(self.response_injector)

	async def is_configured(self, ctx):
		if ctx.guild is None:
			raise commands.NoPrivateMessage()

		if await self.bot.is_owner(ctx.author):
			return True

		if self.bot.guilds.get(ctx.guild.id) is None:
			return False

		return True

	async def can_speak(self, ctx):
		if ctx.guild is None:
			return True

		if not ctx.channel.permissions_for(ctx.guild.me).read_messages:
			return False

		return True

	async def response_injector(self, ctx):
		FORMAT = "{emoji} | {ctx.author.mention}: {content}"

		async def success(content, *args, **kwargs):
			return await ctx.send(FORMAT.format(
				emoji=self.bot.emojis.get("tick", "✅"),
				ctx=ctx,
				content=content
			), *args, **kwargs)

		async def error(content, *args, **kwargs):
			return await ctx.send(FORMAT.format(
				emoji=self.bot.emojis.get("cross", "🚫"),
				ctx=ctx,
				content=content
			), *args, **kwargs)

		ctx.success = success
		ctx.error = error
		
		return True


def setup(bot):
	bot.add_cog(Plugin(bot))