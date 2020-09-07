import core.config as config
import core.constants as constants
import core.logger as logger

from collections import namedtuple
from flask import Flask


version_info = namedtuple("version_info", "name, major, minor, patch, release")
VERSION = version_info(
	name="webcore",
	major=1,
	minor=0,
	patch=0,
	release="stable"
)

class Core(Flask):
	def __init__(self):
		self.log = logger.logger
		self.settings = config.config

		super().__init__("cweb")
		self.secret_key = constants.SECRET_KEY

	def boot(self):
		self.log.info("Running {0.name} v{0.major}.{0.minor}.{0.patch}-{0.release}".format(VERSION))

		try:
			self.run(port=constants.PORT)

		except KeyboardInterrupt:
			self.log.info("Shutting down, reason: manually stopped.")

		except:
			self.log.critical(
				msg="Shutting down, reason: unknown error.",
				exc_info=True
			)