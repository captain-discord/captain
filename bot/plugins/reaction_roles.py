import discord

from discord.ext import commands

from ext.utils import first


class Config:
	def __init__(self, guild, config):
		raw = config.get("reaction_roles", {})

		self.enabled = raw.get("enabled", False)
		self.channel = guild.get_channel(raw.get("channel"))
		self.message_id = raw.get("message")
		self.roles = {guild.get_role(r): e for r, e in raw.get("roles", {}).items()}

	@classmethod
	async def new(cls, bot, guild):
		config = await bot.get_config(guild)
		return cls(guild, config)

	async def message(self):
		if self.channel is not None:
			try:
				return await self.channel.fetch_message(self.message_id)

			except:
				return None

		return None

	def get_for(self, emoji):
		search_result = first(self.roles.items(), lambda r: r[1] == str(emoji))

		if search_result is None:
			return None

		return search_result[0]

class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener("on_raw_reaction_add")
	@commands.Cog.listener("on_raw_reaction_remove")
	async def on_raw_reaction_add_remove(self, payload):
		if payload.guild_id is None:
			return

		guild = self.bot.get_guild(payload.guild_id)
		config = await Config.new(self.bot, guild)

		if payload.message_id != config.message_id or not config.enabled:
			return

		role = config.get_for(payload.emoji)
		member = guild.get_member(payload.user_id)
		message = await config.message()

		if None in (role, member, message):
			return

		if role in member.roles:
			await member.remove_roles(role)

		else:
			await member.add_roles(role)


def setup(bot):
	bot.add_cog(Plugin(bot))