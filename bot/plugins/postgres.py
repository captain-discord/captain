from asyncpg import create_pool
from discord.ext import commands


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_postgres_connect(self):
		"""Handles the creation of required tables when the connection is established."""

		async with self.bot.postgres.acquire() as con:
			queries = ("""CREATE TABLE IF NOT EXISTS infractions (id SERIAL PRIMARY KEY, guild_id BIGINT, actor_id BIGINT, target_id BIGINT, type_id BIGINT, reason TEXT, created_at TIMESTAMP);""",
                       """CREATE TABLE IF NOT EXISTS timers (id SERIAL PRIMARY KEY, event TEXT, expire_at TIMESTAMP, extras JSONB);""",
                       """CREATE TABLE IF NOT EXISTS persistent_roles (id SERIAL PRIMARY KEY, user_id BIGINT, guild_id BIGINT, role_ids TEXT, CONSTRAINT unique_user_guild UNIQUE (user_id, guild_id));""",
                       """CREATE TABLE IF NOT EXISTS starboard_messages (id SERIAL PRIMARY KEY, guild_id BIGINT, starboard_id BIGINT, channel_id BIGINT, message_id BIGINT, created_at TIMESTAMP);""",
					   """CREATE TABLE IF NOT EXISTS message_archives (id SERIAL PRIMARY KEY, cdn_url TEXT, key TEXT);""")

			for query in queries:
				await con.execute(query)

def setup(bot):
	if bot.config is None:
		return bot.log.warn("Can't connect to Postgres, reason: no external config file.")

	try:
		bot.postgres = bot.loop.run_until_complete(create_pool(bot.config["postgres"]))

		bot.log.info("Successfully connected to Postgres server.")
		bot.add_cog(Plugin(bot))
		bot.dispatch("postgres_connect")

	except:
		bot.log.fatal("Can't connect to Postgres, reason: error occured when making connection.", exc_info=True)