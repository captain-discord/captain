import discord

from datetime import datetime
from discord.ext import commands

from ext.utils import shorten


def get_emoji(stars):
	if 5 > stars >= 0:
		return "\N{WHITE MEDIUM STAR}"

	elif 10 > stars >= 5:
		return "\N{GLOWING STAR}"

	elif 25 > stars >= 10:
		return "\N{DIZZY SYMBOL}"

	else:
		return "\N{SPARKLES}"

def get_gradient(stars):
	p = stars / 13
	if p > 1.0:
		p = 1.0

	return (255 << 16) + (int((194 * p) + (253 * (1 - p))) << 8) + int((12 * p) + (247 * (1 - p)))

def create_message(message, stars):
	"""Creates the embed and message content for a starboard message."""

	IMAGE_EXTENSIONS = ("png", "jpeg", "jpg", "gif", "webp")

	content = f"{get_emoji(stars)} **{stars}** | {message.channel.mention}"

	if message.channel.is_nsfw():
		content += " :rotating_light: **NSFW** :rotating_light:"

	embed = discord.Embed(
		colour=get_gradient(stars),
		description=shorten(f"[Click here to jump!]({message.jump_url})\n\n{(message.content if not message.channel.is_nsfw() else f'||{message.content}||') if message.content else ''}", 1000),
		timestamp=message.created_at
	)
	embed.set_author(
		name=f"{message.author.display_name}#{message.author.discriminator}", 
		icon_url=message.author.avatar_url
	)
	embed.set_footer(text=f"ID: {message.id}")

	if message.embeds:
		data = message.embeds[0]
		if data.type == "rich":
			embed_value = ""

			if data.image:
				embed_value += f"[Image]({data.image.url})\n"

			if data.thumbnail:
				embed_value += f"[Thumbnail]({data.thumbnail.url})\n"

			if data.description:
				embed_value += f"{data.description}\n" if not message.channel.is_nsfw() else f"||{data.description}||\n"

			if data.fields:
				embed_value += "\n".join((f"__**{field.name}**__\n{field.value}" if not message.channel.is_nsfw() else f"||__**{field.name}**__\n{field.value}||") for field in data.fields)

			if embed_value:
				embed.add_field(
					name=data.title if data.title else "No title",
					value=shorten(embed_value, 1000)
				)

	if message.attachments:
		if not message.channel.is_nsfw():
			first_file = message.attachments[0]
			if first_file.url.lower().endswith(IMAGE_EXTENSIONS):
				embed.set_image(first_file.url)

		attach_content = ""
		for attachment in message.attachments:
			buffer = f"[{attachment.filename}]({attachment.url})\n"

			if len(attach_content + buffer) > 950:
				attach_content += f"\n*See the original message for all {len(message.attachments)} attachments.*"
				break

			attach_content += buffer

		embed.add_field(
			name=f"Attachments ({len(message.attachments)})", 
			value=attach_content, 
			inline=False
		)

	return content, embed


class Config:
	def __init__(self, bot, guild):
		self.bot = bot
		self.guild = guild

		if isinstance(guild, int):
			self.guild = bot.get_guild(guild)

		self.raw = bot.guilds.get(self.guild.id, {}).get("starboard", {})

		self.enabled = self.raw.get("enabled", False)
		self.emoji = self.raw.get("emoji", "⭐")
		self.required = self.raw.get("required_stars", 3)
		self.channel = bot.get_channel(self.raw.get("channel"))

		self.ignored_roles = list(filter(None, [self.guild.get_role(r) for r in self.raw.get("ignored_roles", [])]))
		self.ignored_channels = list(filter(None, [self.guild.get_channel(c) for c in self.raw.get("ignored_channels", [])]))

	def is_ignored(self, user, channel):
		if channel in self.ignored_channels:
			return True

		for r in self.ignored_roles:
			if r in user.roles:
				return True

		return False


class Plugin(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.Cog.listener()
	async def on_raw_message_delete(self, payload):
		if payload.guild_id is None:
			return

		config = Config(self.bot, payload.guild_id)

		if not config.enabled or config.channel is None or payload.channel_id == config.channel.id:
			return

		async with self.bot.postgres.acquire() as con:
			query = """SELECT starboard_id FROM starboard_messages
					   WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3;"""

			existing_message = await con.fetchval(query, payload.guild_id, payload.message_id, payload.channel_id)
			if existing_message is None:
				starboard_message = None
			
			else:
				try:
					starboard_message = await config.channel.fetch_message(existing_message)

				except:
					return

		async with self.bot.postgres.acquire() as con:
			query = """DELETE FROM starboard_messages 
					   WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3;"""

			await con.execute(query, payload.guild_id, payload.message_id, payload.channel_id)
			await starboard_message.delete()


	@commands.Cog.listener("on_raw_reaction_add")
	@commands.Cog.listener("on_raw_reaction_remove")
	async def update_starboard(self, payload):
		if payload.guild_id is None:
			return

		config = Config(self.bot, payload.guild_id)

		if not config.enabled or config.channel is None or str(payload.emoji) != config.emoji or payload.channel_id == config.channel.id or payload.channel_id in config.ignored_channels:
			return

		channel = self.bot.get_channel(payload.channel_id)
		message = await channel.fetch_message(payload.message_id)

		if config.is_ignored(message.author, message.channel):
			return

		async with self.bot.postgres.acquire() as con:
			query = """SELECT starboard_id FROM starboard_messages
					   WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3;"""

			existing_message = await con.fetchval(query, payload.guild_id, payload.message_id, payload.channel_id)
			if existing_message is None:
				starboard_message = None
			
			else:
				try:
					starboard_message = await config.channel.fetch_message(existing_message)

				except:
					return

			async def _delete(message):
				query = """DELETE FROM starboard_messages 
						   WHERE guild_id = $1 AND message_id = $2 AND channel_id = $3;"""

				await con.execute(query, payload.guild_id, payload.message_id, payload.channel_id)
				await message.delete()

			star_reaction = [reaction for reaction in message.reactions if str(reaction.emoji) == config.emoji]
			if not star_reaction:
				if starboard_message is None:
					return

				return await _delete(starboard_message)

			stars = len([starrer for starrer in await star_reaction[0].users().flatten() if starrer != message.author and not [r for r in starrer.roles if r in config.ignored_roles]])
			if stars < config.required:
				if starboard_message:
					await _delete(starboard_message)

				return

			content, embed = create_message(message, stars)

			async def _new_msg():
				query = """INSERT INTO starboard_messages (guild_id, starboard_id, message_id, channel_id, created_at)
						   VALUES ($1, $2, $3, $4, $5);"""

				msg = await config.channel.send(content,
					embed=embed
				)

				await con.execute(query, payload.guild_id, msg.id, payload.message_id, payload.channel_id, datetime.utcnow())

			if not existing_message:
				await _new_msg()

			else:
				if starboard_message is None:
					await _new_msg()

				else:
					await starboard_message.edit(
						content=content,
						embed=embed
					)


def setup(bot):
	bot.add_cog(Plugin(bot))