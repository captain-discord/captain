from datetime import datetime
from discord.ext import commands

from plugins.infractions import Handler as InfractionHandler


class Config:
	def __init__(self, bot, guild):
		self.bot = bot
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.configs.get(self.guild.id, {}).get("bot_filter", {})

		self.enabled = self.raw.get("enabled", False)
		self.require_verification = self.raw.get("require_verification", True)
		self.min_age = self.raw.get("min_age", 86400)

		self.whitelist = self.raw.get("whitelist", [])


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if not member.bot or not member.guild.me.guild_permissions.kick_members:
			return

		config = Config(self.bot, member.guild)
		handler = InfractionHandler(self.bot, member.guild)
		
		if not config.enabled or member.id in config.whitelist:
			return

		if config.require_verification and not member.public_flags.verified_bot:
			await handler.kick(member.guild.me, member, "Doesn't meet filter requirements (missing verified flag).")

		elif (datetime.utcnow() - member.created_at).total_seconds() < config.min_age:
			await handler.kick(member.guild.me, member, "Doesn't meet filter requirements (account too young).")


def setup(bot):
	bot.add_cog(Plugin(bot))