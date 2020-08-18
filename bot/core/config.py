import core.constants as constants
import core.enumerators as enums

from discord import Message
from discord.ext import commands
from importlib import import_module


# Here we're loading the config file according to the options specified in constants.py
if constants.CONFIG_ENABLED:
	# JSON formatting
	if constants.CONFIG_FORMAT == enums.ConfigFormatterEnum.JSON:
		from json import load

		config = load(open(constants.CONFIG_PATH))

	# YAML formatting
	elif constants.CONFIG_FORMAT == enums.ConfigFormatterEnum.YAML:
		from yaml import safe_load

		config = safe_load(open(constants.CONFIG_PATH))

	# TOML formatting
	elif constants.CONFIG_FORMAT == enums.ConfigFormatterEnum.TOML:
		from toml import load

		config = load(constants.CONFIG_PATH)

	# Native formatting
	elif constants.CONFIG_FORMAT == enums.ConfigFormatterEnum.NATIVE:
		mod = import_module(constants.CONFIG_PATH)
		
		config = mod.CONFIG

	else:
		config = {}

else:
	config = None