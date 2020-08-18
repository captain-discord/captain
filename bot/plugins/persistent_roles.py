import discord

from ast import literal_eval
from discord.ext import commands

from plugins.logging import Handler as LoggingHandler
from plugins.infractions import Handler as InfractionHandler


class Config:
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id, {}).get("persistent_roles", {})
		
		self.enabled = self.raw.get("enabled", False)
		self.whitelist = list(filter(None, [self.guild.get_role(r) for r in self.raw.get("whitelist", [])]))


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	async def sync(self, member):
		if not member.guild.me.guild_permissions.manage_roles:
			return

		config = Config(self.bot, member.guild)

		if not config.enabled:
			return

		async with self.bot.postgres.acquire() as con:
			query = """INSERT INTO persistent_roles (user_id, guild_id, role_ids)
					   VALUES ($1, $2, $3)
					   ON CONFLICT ON CONSTRAINT unique_user_guild
					   DO UPDATE SET role_ids = $3;"""

			await con.execute(query, member.id, member.guild.id, str([r.id for r in member.roles]))

	# by synchronising both when the user's roles update and when they leave the server,
	# we can avoid a state condition where the roles stored are out-of-sync because
	# the bot experienced some downtime

	# the normal solution would be to perform a synchronisation of the entire guild at startup
	# which is costly and annoying to program

	# instead, we can achieve the same result by making sure that we grab the role set when
	# they leave as well, which means we recover the lost events from the downtime

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		await self.sync(member)

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if before.roles == after.roles:
			return 

		await self.sync(after)

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if not member.guild.me.guild_permissions.manage_roles:
			return

		config = Config(self.bot, member.guild)
		mute_role = InfractionHandler(self.bot, member.guild).mute_role

		if not config.enabled:
			return

		async with self.bot.postgres.acquire() as con:
			query = """SELECT role_ids FROM persistent_roles
					   WHERE user_id = $1 AND guild_id = $2;"""

			roles = await con.fetchval(query, member.id, member.guild.id)

			if not roles:
				return

		for role in literal_eval(roles):
			role = member.guild.get_role(role)

			if role not in config.whitelist:
				continue

			if role in (None, member.guild.default_role):
				continue

			if role.position >= member.guild.me.top_role.position:
				continue

			if role == mute_role:
				await LoggingHandler(self.bot, member.guild).dispatch("MEMBER_REMUTE",
					user_to_dm=member,
					target=member
				)

			await member.add_roles(role,
				reason="Persisted role."
			)


def setup(bot):
	bot.add_cog(Plugin(bot))