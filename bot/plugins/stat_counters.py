import discord

from datetime import datetime
from discord.ext import commands


class Counter:
	def __init__(self, bot, id, **options):
		self.channel = bot.get_channel(id)
		self.event = options.get("event")
		self.format = options.get("format")

class Config:
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.configs.get(self.guild.id, {}).get("stat_counters", {})
		self.counters = [Counter(bot, id, **options) for id, options in self.raw.items()]

	def get(self, events):
		return [c for c in self.counters if c.event in events]

class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener("on_member_remove")
	@commands.Cog.listener("on_member_join")
	async def on_member_count_change(self, member):
		config = Config(self.bot, member.guild)

		events = ["MEMBER_COUNT_CHANGE"]
		if member not in member.guild.members:
			events.append("NEWEST_MEMBER")

		if member.bot:
			events.append("BOT_COUNT_CHANGE")
			if member not in member.guild.members:
				events.append("NEWEST_BOT")

		else:
			events.append("HUMAN_COUNT_CHANGE")
			if member not in member.guild.members:
				events.append("NEWEST_HUMAN")

		new_value = {
			"MEMBER_COUNT_CHANGE": member.guild.member_count,
			"HUMAN_COUNT_CHANGE": len([member for member in member.guild.members if not member.bot]),
			"BOT_COUNT_CHANGE": len([member for member in member.guild.members if member.bot]),

			"NEWEST_MEMBER": member,
			"NEWEST_HUMAN": member,
			"NEWEST_BOT": member
		}

		for counter in config.get(events):
			if counter.channel is None:
				continue
			
			await counter.channel.edit(
				name=counter.format.format(value=new_value.get(counter.event))
			)


def setup(bot):
	bot.add_cog(Plugin(bot))