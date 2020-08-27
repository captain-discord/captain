import menus

import core.prefix as prefix

from discord import Embed
from discord.ext import commands

from ext.exceptions import LookupFailed
from ext.state import access_control
from ext.utils import time_since


class CommandSet:
	def __init__(self, container):
		self.container = container

	@property
	def commands(self):
		if isinstance(self.container, commands.Group):
			command_list = list(self.container.commands)
			command_list.insert(0, self.container)

			return command_list

		if isinstance(self.container, commands.Command):
			return self.container,

		return self.container.get_commands()

	@property
	def description(self):
		return self.container.description

	@property
	def name(self):
		if isinstance(self.container, commands.Cog):
			return self.container.qualified_name

		return self.container.name.title()


class Plugin(commands.Cog, command_attrs=dict(hidden=True)):
	def __init__(self, bot):
		self.bot = bot

	class HelpSource(menus.GroupByPageSource):
		def __init__(self, command_sets, help_usage):
			self.help_usage = help_usage

			super().__init__(
				entries=command_sets,
				per_page=1,
				key=None,
				sort=False
			)

		async def format_page(self, menu, entry):
			command_set = entry.items[0]

			embed = Embed(
				colour=0x7289DA,
				title=command_set.name,
				description=command_set.description
			)
			
			embed.set_author(name=f"Page {menu.current_page + 1}/{self.get_max_pages()} ({len(command_set.commands)} commands)")
			embed.set_footer(text=f"Use {prefix.default}{self.help_usage} for more help.")

			for command in command_set.commands:
				description = command.short_doc

				if hasattr(command.callback, "__commands_cooldown__"):
					cooldown = command.callback.__commands_cooldown__
					
					cooldown_type = {
						commands.BucketType.default: "at any time",
						commands.BucketType.user: "per user",
						commands.BucketType.channel: "per channel",
						commands.BucketType.guild: "per server",
						commands.BucketType.category: "per channel category",
						commands.BucketType.member: "per server member",
						commands.BucketType.role: "per server role",
					}[cooldown.type]

					description += f"\n\n**Cooldown: {cooldown.rate} every {time_since(seconds=cooldown.per)} {cooldown_type}**"

				if isinstance(command, commands.Group):
					description += f"\n\n*Use **{prefix.default}help {command.name}** for a list of subcommands.*"

				embed.add_field(
					name=command.usage,
					value=description,
					inline=False
				)

			return embed


	class HelpMenu(menus.MenuPages):
		def __init__(self, source):
			super().__init__(
				source=source, 
				clear_reactions_after=True
			)

	@access_control.require(access_control.Level.DEFAULT)
	@commands.command("help",
		usage="help [command|category:text]",
		aliases=["commands"]
	)
	async def help(self, ctx, *, command_lookup: str = None):
		command_sets = []
		if command_lookup is None:
			for cog in self.bot.cogs.values():
				cog_commands = [command for command in cog.get_commands() if not command.hidden]

				if not cog_commands:
					continue

				command_sets.append(CommandSet(cog))

		else:
			found = self.bot.get_command(command_lookup)

			if found is None:
				raise LookupFailed("commands")

			command_sets.append(CommandSet(found))

		await self.HelpMenu(self.HelpSource(command_sets, ctx.command.usage)).start(ctx)


def setup(bot):
	bot.remove_command("help")
	bot.add_cog(Plugin(bot))