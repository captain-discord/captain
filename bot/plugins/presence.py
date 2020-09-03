import discord

import core.constants as constants

from discord.ext import commands, tasks

status: discord.Status  = constants.PRESENCE_STATUS
name: str = constants.PRESENCE_NAME
type: discord.ActivityType = constants.PRESENCE_TYPE
enabled: bool = constants.PRESENCE_ENABLED
url: str = constants.PRESENCE_URL


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

		if enabled:
			self.presence_maintainer.start()

	@tasks.loop(seconds=3600)
	async def presence_maintainer(self):
		await self.bot.change_presence(
			activity=discord.Activity(
				type=type,
				name=name.format(
					guilds=len(self.bot.guilds),
					users=len(self.bot.users)
				),
				url=url
			),
			status=status
		)
		self.bot.log.debug("Re-sent presence information.")

	@presence_maintainer.before_loop
	async def presence_maintainer_wait(self):
		await self.bot.wait_until_ready()


def setup(bot):
	bot.add_cog(Plugin(bot))