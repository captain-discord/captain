import discord

from datetime import datetime
from discord.ext import commands
from ext.utils import ordinal_indicator, time_since


class Handler:
	def __init__(self, bot, guild, config):
		self.bot = bot
		self.guild = guild

		self.logs = {self.guild.get_channel(cid): e for cid, e in config.get("logs", {}).items()}

	@classmethod
	async def new(cls, bot, guild):
		config = await bot.get_config(guild)
		return cls(bot, guild, config)

	def dm_fail_format(self, event, target):
		base = self.bot.actions.get("dm_fail_base")
		infr_name = self.bot.actions.get(event, {}).get("infraction", "???")

		return base.format(
			at=datetime.utcnow().strftime(self.bot.actions.get("time_format")),
			target=target,
			infraction=infr_name
		)

	def dm_format(self, event, **options):
		base = self.bot.actions.get("base")
		dm_base = self.bot.actions.get(event, {}).get("dm")

		return base.format(
			at=datetime.utcnow().strftime(self.bot.actions.get("time_format")),
			emoji=self.bot.actions.get(event, {}).get("emoji"),
			text=dm_base.format(
				guild=self.guild,
				**options
			)
		)

	def log_format(self, event, **options):
		base = self.bot.actions.get("base")
		log_base = self.bot.actions.get(event, {}).get("text")

		return base.format(
			at=datetime.utcnow().strftime(self.bot.actions.get("time_format")),
			emoji=self.bot.actions.get(event, {}).get("emoji"),
			text=log_base.format(**options)
		)

	async def dispatch(self, event, user_to_dm=None, **options):
		logs = [c for c, e in self.logs.items() if event in e]
		failed_to_dm = False

		if user_to_dm is not None:
			if user_to_dm.bot:
				failed_to_dm = True

			else:
				try:
					await user_to_dm.send(self.dm_format(event, **options))

				except:
					failed_to_dm = True

		for log in logs:
			if log is None:
				continue

			await log.send(self.log_format(event, **options))
			if failed_to_dm:
				await log.send(self.dm_fail_format(event, user_to_dm))

class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_message_edit(self, before, after):
		if after.content == before.content:
			return
		
		log = await Handler.new(self.bot, after.guild)
		await log.dispatch("MESSAGE_EDIT",
			before=before,
			after=after
		)

	@commands.Cog.listener()
	async def on_message_delete(self, message):
		if not message.content:
			return
		
		log = await Handler.new(self.bot, message.guild)
		await log.dispatch("MESSAGE_DELETE",
			message=message
		)

	@commands.Cog.listener()
	async def on_raw_bulk_message_delete(self, payload):
		log = await Handler.new(self.bot, payload.guild_id)
		await log.dispatch("MESSAGE_BULK_DELETE",
			amount=len(payload.message_ids),
			channel=self.bot.get_channel(payload.channel_id)
		)
	
	@commands.Cog.listener()
	async def on_member_join(self, member):
		log = await Handler.new(self.bot, member.guild)
		await log.dispatch("MEMBER_JOIN",
			user=member,
			ordinal=ordinal_indicator(member.guild.member_count)
		)

	@commands.Cog.listener()
	async def on_member_remove(self, member):
		log = await Handler.new(self.bot, member.guild)
		await log.dispatch("MEMBER_LEAVE",
			user=member,
			joined_ago=time_since(since=member.joined_at)
		)

	@commands.Cog.listener("on_guild_channel_delete")
	@commands.Cog.listener("on_guild_role_delete")
	async def channel_or_role_delete(self, channel_or_role):
		if isinstance(channel_or_role, discord.Role):
			event = "ROLE_DELETE"
			kwargs = {"role": channel_or_role}

		else:
			event = "CHANNEL_DELETE"
			kwargs = {"channel": channel_or_role}

		log = await Handler.new(self.bot, channel_or_role.guild)
		await log.dispatch(event,
			**kwargs
		)

	@commands.Cog.listener("on_guild_channel_create")
	@commands.Cog.listener("on_guild_role_create")
	async def channel_or_role_create(self, channel_or_role):
		if isinstance(channel_or_role, discord.Role):
			event = "ROLE_CREATE"
			kwargs = {"role": channel_or_role}

		else:
			event = "CHANNEL_CREATE"
			kwargs = {"channel": channel_or_role}

		log = await Handler.new(self.bot, channel_or_role.guild)
		await log.dispatch(event,
			**kwargs
		)

	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		if before.nick == after.nick:
			return

		if after.nick is None:
			event = "NICKNAME_REMOVE"
			kwargs = {
				"user": after,
				"nick": before.nick
			}

		elif before.nick is None:
			event = "NICKNAME_ADD"
			kwargs = {
				"user": after,
				"nick": after.nick
			}

		else:
			event = "NICKNAME_CHANGE"
			kwargs = {
				"user": after,
				"before": before.nick,
				"after": after.nick
			}

		log = await Handler.new(self.bot, after.guild)
		await log.dispatch(event,
			**kwargs
		)


def setup(bot):
	bot.add_cog(Plugin(bot))