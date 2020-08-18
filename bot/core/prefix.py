import core.constants as constants

from discord import Message
from discord.ext import commands

default: str  = constants.PREFIX_DEFAULT
aliases: list = constants.PREFIX_ALIASES
mention: bool = constants.PREFIX_MENTION

def all(bot: commands.Bot) -> list:
	"""Returns a list of all possible prefixes."""

	return [default, *aliases] + ([bot.user.mention] if mention else [])

def processor(bot: commands.Bot,
			  msg: Message) -> callable:
	"""This is what gets forwarded to command_prefix in the core."""

	prefixes = aliases
	prefixes.insert(0, default)
	
	if mention:
		if isinstance(prefixes, str):
			prefixes = prefixes,

		return commands.when_mentioned_or(*prefixes)(bot, msg)

	return prefixes