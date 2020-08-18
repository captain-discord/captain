import core.config as config
import core.constants as constants
import core.logger as logger
import core.prefix as prefix

from asyncio import all_tasks
from collections import namedtuple
from discord.ext import commands


# This describes the version of the core itself, I don't recommend changing this at all.
# If you want to create version information specific to your bot, create a variable in the file that calls Core.boot.
version_info = namedtuple("version_info", "name, major, minor, patch, release")
VERSION = version_info(
	name="pycore",
	major=1,
	minor=0,
	patch=0,
	release="stable"
)


class Core(commands.Bot):
	async def shutdown(self):
		"""This calmly and quietly closes the running event loops and any tasks.
		
		This exists with a status code of 2."""

		try:
			for task in all_tasks():
				try: 
					task.cancel()

				except: 
					continue

		except RuntimeError: 
			pass
		
		try:
			await self.logout()
			self.loop.stop()
			self.loop.close()
		
		except: 
			pass

		quit()

	def __init__(self):
		self.log = logger.logger
		self.config = config.config
		self.prefix = prefix

		super().__init__(
			command_prefix=prefix.processor,
			owner_ids=constants.OWNER_IDS,
			max_messages=constants.MESSAGE_CACHE_SIZE
		)

	def boot(self):
		"""Plugins are loaded here just prior to initialising the gateway connection."""

		self.log.debug(f"Attempting to load {len(constants.PLUGINS)} plugins.")
		for index, plugin in enumerate(constants.PLUGINS):
			try:
				self.load_extension(plugin)
				self.log.debug(f"Successfully loaded plugin {plugin} ({index}/{len(constants.PLUGINS)})")

			except commands.ExtensionFailed:
				self.log.fatal(
					msg=f"Couldn't load plugin {plugin} failed to load.",
					exc_info=True
				)
				quit()

		self.log.info(f"All {len(constants.PLUGINS)} plugins have been loaded.")
		self.log.info("Running {0.name} v{0.major}.{0.minor}.{0.patch}-{0.release}".format(VERSION))

		try:
			self.run(constants.TOKEN)

		except KeyboardInterrupt:
			self.log.info("Shutting down, reason: manually stopped.")

		except:
			self.log.critical(
				msg="Shutting down, reason: unknown error.",
				exc_info=True
			)