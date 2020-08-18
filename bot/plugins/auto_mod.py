import re

from discord.ext import commands

from plugins.infractions import Handler as InfractionHandler


class ConfigMixin:
	def __init__(self, bot, guild, config):
		self._handler = InfractionHandler(bot, guild)

		self.enabled = config.get("enabled", False)
		self.duration = config.get("duration", None)

		self._response = {
			0: self._handler.ban,
			1: self._handler.kick,
			2: self._handler.mute,
			3: self._handler.warn,
			4: None
		}.get(config.get("action", None))

		self.ignored_roles = list(filter(None, [guild.get_role(r) for r in config.get("ignored_roles", [])]))
		self.ignored_channels = list(filter(None, [guild.get_channel(c) for c in config.get("ignored_channels", [])]))

	async def respond(self, user, reason):
		AVAILABLE_TEMP_RESPONSES = self._handler.ban, self._handler.mute

		if self._response is None:
			return 
		
		if self._response in AVAILABLE_TEMP_RESPONSES:
			return await self._response(self.guild.me, user, reason, self.duration)

		else:
			return await self._response(self.guild.me, user, reason)

	def is_ignored(self, user, channel):
		if channel in self.ignored_channels:
			return True

		for r in self.ignored_roles:
			if r in user.roles:
				return True

		return False

class CountMixin:
	def __init__(self, config):
		self.count = config.get("count", 5)
		self.threshold = config.get("threshold", 5)

class SpamConfig(ConfigMixin, CountMixin):
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id).get("anti_spam", {})

		ConfigMixin.__init__(self, bot, guild, self.raw)
		CountMixin.__init__(self, self.raw)

class PingSpamConfig(ConfigMixin, CountMixin):
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id).get("anti_ping_spam", {})

		ConfigMixin.__init__(self, bot, guild, self.raw)
		CountMixin.__init__(self, self.raw)

class CurseConfig(ConfigMixin):
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id).get("anti_curse", {})
		self.blacklist = self.raw.get("blacklist", [])

		ConfigMixin.__init__(self, bot, guild, self.raw)

class InviteConfig(ConfigMixin):
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id).get("anti_invite", {})
		self.whitelist = self.raw.get("whitelist", [])

		ConfigMixin.__init__(self, bot, guild, self.raw)

class AutoRoleConfig:
	def __init__(self, bot, guild):
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id).get("auto_roles", {})
		self.bot = list(filter(None, [self.guild.get_role(r) for r, e in self.raw.items() if "BOT" in e]))
		self.human = list(filter(None, [self.guild.get_role(r) for r, e in self.raw.items() if "HUMAN" in e]))

class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener("on_message")
	async def anti_spam(self, message):
		if message.guild is None:
			return

		config = SpamConfig(self.bot, message.guild)

		if message.author in (self.bot.user, message.guild.owner) or not config.enabled or config.is_ignored(message.author, message.channel):
			return

		count = self.bot.redis.incr(f"spam:{message.guild.id}:{message.author.id}")
		self.bot.redis.expire(f"spam:{message.guild.id}:{message.author.id}", config.threshold)

		if count > config.count - 1:
			if message.guild.me.guild_permissions.manage_messages:
				await message.channel.purge(
					limit=config.count,
					check=lambda m: m.author == message.author
				)

			await config.respond(message.author, f"Spam detected in #{message.channel} ({config.count}/{config.threshold}s)")

	@commands.Cog.listener("on_message")
	async def anti_ping_spam(self, message):
		if message.guild is None:
			return

		config = PingSpamConfig(self.bot, message.guild)

		if message.author in (self.bot.user, message.guild.owner) or not message.mentions or not config.enabled or config.is_ignored(message.author, message.channel):
			return

		count = self.bot.redis.incr(f"ping:{message.guild.id}:{message.author.id}")
		self.bot.redis.expire(f"ping:{message.guild.id}:{message.author.id}", config.threshold)

		if count > config.count - 1:
			if message.guild.me.guild_permissions.manage_messages:
				await message.delete()

			await config.respond(message.author, f"Ping spam detected in #{message.channel} ({config.count}/{config.threshold}s)")

	@commands.Cog.listener("on_message")
	async def anti_curse(self, message):
		if message.guild is None:
			return

		config = CurseConfig(self.bot, message.guild)

		if message.author in (self.bot.user, message.guild.owner) or not config.enabled or config.is_ignored(message.author, message.channel):
			return

		for word in config.blacklist:
			if word in message.content:
				if message.guild.me.guild_permissions.manage_messages:
					await message.delete()

				await config.respond(message.author, f"Censored word detected in #{message.channel}")

	@commands.Cog.listener("on_message")
	async def anti_invite(self, message):
		if message.guild is None:
			return

		config = InviteConfig(self.bot, message.guild)

		if message.author in (self.bot.user, message.guild.owner) or not config.enabled or config.is_ignored(message.author, message.channel):
			return

		REGEX = r"(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/.+[a-z]"
		whitelisted_partial = "|".join(whitelist for whitelist in config.whitelist)
		match = [m.group() for m in re.finditer(REGEX, message.content, re.IGNORECASE)]

		if not match:
			return

		if message.guild.me.guild_permissions.manage_guild:
			invites = "|".join(invite.code for invite in await message.guild.invites())

		for invite in match[0].split(" "):
			if not re.search(REGEX, invite, re.IGNORECASE):
				continue

			if whitelisted_partial:
				if re.search(rf"(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/({whitelisted_partial})", invite, re.IGNORECASE):
					continue

			if message.guild.me.guild_permissions.manage_guild:
				if re.search(rf"(https?:\/\/)?(www\.)?(discord\.gg|discord\.com\/invite)\/({invites})", invite, re.IGNORECASE) and invites:
					continue

			if message.guild.me.guild_permissions.manage_messages:
				await message.delete()

			await config.respond(message.author, f"Invite detected in #{message.channel}")
			break

	@commands.Cog.listener()
	async def on_member_join(self, member):
		if member.guild.me.guild_permissions.manage_roles:
			config = AutoRoleConfig(self.bot, member.guild)

			if member.bot:
				roles = config.bot

			else:
				roles = config.human

			await member.add_roles(*roles)
   
	@commands.Cog.listener()
	async def on_ready(self):
		for guild in self.bot.guilds:
			config = AutoRoleConfig(self.bot, guild)

			if not config.human and not config.bot:
				continue

			for member in config.guild.members:
				if member.bot:
					roles = config.bot

				else:
					roles = config.human

				for role in roles:
					if role not in member.roles:
						await member.add_roles(role)


def setup(bot):
	bot.add_cog(Plugin(bot))