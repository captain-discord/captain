import discord

from discord.ext import commands
from redis import Redis


def setup(bot: commands.Bot):
	if bot.config is None:
		return bot.log.warn("Can't connect to Redis, reason: no external config file.")

	config = bot.config.get("redis", {})

	try:
		bot.redis = Redis(
			host=config.get("host", "127.0.0.1"),
			port=config.get("port", "6379"),
			password=config.get("password"),
			db=config.get("database", 0)
		)
		bot.redis.ping()

		bot.log.info("Successfully connected to Redis server.")

	except:
		bot.log.fatal( "Can't connect to Redis, reason: error occured when making connection.", exc_info=True)