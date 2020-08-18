from core import Core, version_info
from yaml import safe_load

VERSION = version_info(
	name="captain",
	major=3,
	minor=0,
	patch=0,
	release="rc1"
)

class PatchedCore(Core):
	actions = None
	emojis = None
	guilds = None

bot = PatchedCore()

bot.actions = safe_load(open("actions.yml"))
bot.emojis = safe_load(open("emojis.yml"))
bot.guilds = safe_load(open("guilds.yml"))

bot.log.info("Running {0.name} v{0.major}.{0.minor}.{0.patch}-{0.release}".format(VERSION))
bot.boot()