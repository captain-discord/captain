import discord

import core.prefix as prefix

from discord.ext import commands


class ActionEnum:
	SEND_MESSAGE = 0
	TOGGLE_ROLE  = 1


class Command:
	def __init__(self, bot, **options):
		self.bot = bot

		self.name = options.pop("name")
		self.action = options.pop("action")
		self.value = options.pop("value")

	def triggers(self):
		result = []
		for p in prefix.all(self.bot):
			# we have to ommit mentions here as it doesn't seem to work,
			# might investigate and try to fix one day
			if p != self.bot.user.mention:
				result.append(f"{p}{self.name}")

		return result

class Config:
	def __init__(self, bot, guild, config):
		self.commands = [Command(bot, **c) for c in config.get("custom_commands", [])]

	@classmethod
	async def new(cls, bot, guild):
		config = await bot.get_config(guild)
		return cls(bot, guild, config)


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message(self, message):
		config = await Config.new(self.bot, message.guild)

		if not config.commands:
			return

		for command in config.commands:
			if message.content.startswith(tuple(command.triggers())):
				if command.action == ActionEnum.SEND_MESSAGE:
					return await message.channel.send(command.value.format(ctx=message))

				elif command.action == ActionEnum.TOGGLE_ROLE:
					role = message.guild.get_role(command.value)
					if role is None:
						return await message.channel.send(f"{self.bot.emojis.get('cross', '❌')} | {message.author.mention}: The configured role for this command doesn't exist, please contact a server Administrator!")

					if role.position >= message.guild.me.top_role.position:
						return await message.channel.send(f"{self.bot.emojis.get('cross', '❌')} | {message.author.mention}: The role is too high for me to add it to users, please contact a server Administrator!")

					if not message.guild.me.guild_permissions.manage_roles:
						return await message.channel.send(f"{self.bot.emojis.get('cross', '❌')} | {message.author.mention}: I'm missing the `manage_roles` permission, please contact a server Administrator!")

					try:
						if role in message.author.roles:
							await message.author.remove_roles(role)
							await message.channel.send(f"{self.bot.emojis.get('tick', '✅')} | {message.author.mention}: I've removed the {role} role from you!")

						else:
							await message.author.add_roles(role)
							await message.channel.send(f"{self.bot.emojis.get('tick', '✅')} | {message.author.mention}: I've given you the {role} role!")

					except discord.HTTPException:
						return await message.channel.send(f"{self.bot.emojis.get('cross', '❌')} | {message.author.mention}: Something went wrong when trying to toggle the role, please contact a server Administrator!")


def setup(bot):
	bot.add_cog(Plugin(bot))