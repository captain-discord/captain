import base64, discord, html, re

from datetime import datetime
from discord.ext import commands
from ext.utils import bytes_4_humans, identifier
from os import remove

from ext.exceptions import MissingSubcommand
from ext.state import access_control

# the majority of this function was "borrowed" from kyb3r's modmail logviewer
# https://github.com/kyb3r/logviewer/blob/master/core/formatter.py
def format_content_html(content, allow_links=False):
	def encode_codeblock(m):
		encoded = base64.b64encode(m.group(1).encode()).decode()

		return f"\x1AM{encoded}\x1AM"

	# Encode multiline codeblocks (```text```)
	content = re.sub(r"```+((?:[^`]*?\n)?(?:[^`]+))\n?```+", encode_codeblock, content)
	content = html.escape(content)

	def encode_inline_codeblock(m):
		encoded = base64.b64encode(m.group(1).encode()).decode()

		return f"\x1AI{encoded}\x1AI"

	# Encode inline codeblocks (`text`)
	content = re.sub(r"`([^`]+)`", encode_inline_codeblock, content)

	# Encode links
	if allow_links:
		def encode_link(m):
			encoded_1 = base64.b64encode(m.group(1).encode()).decode()
			encoded_2 = base64.b64encode(m.group(2).encode()).decode()

			return f"\x1AL{encoded_1}|{encoded_2}\x1AL"

		content = re.sub(r"\[(.*?)\]\((.*?)\)", encode_link, content)

	def encode_url(m):
		encoded = base64.b64encode(m.group(1).encode()).decode()

		return f"\x1AU{encoded}\x1AU"

	# Encode URLs
	content = re.sub(r"(\b(?:(?:https?|ftp|file)://|www\.|ftp\.)(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,\.\[\];]*\)|[-a-zA-Z0-9+&@#/%?=~_|!:,\.\[\];])*(?:\([-a-zA-Z0-9+&@#/%?=~_|!:,\.\[\];]*\)|[-a-zA-Z0-9+&@#/%=~_|$]))", encode_url, content)

	# Process bold (**text**)
	content = re.sub(r"(\*\*)(?=\S)(.+?[*_]*)(?<=\S)\1", r"<b>\2</b>", content)

	# Process underline (__text__)
	content = re.sub(r"(__)(?=\S)(.+?)(?<=\S)\1", r"<u>\2</u>", content)

	# Process italic (*text* or _text_)
	content = re.sub(r"(\*|_)(?=\S)(.+?)(?<=\S)\1", r"<i>\2</i>", content)

	# Process strike through (~~text~~)
	content = re.sub(r"(~~)(?=\S)(.+?)(?<=\S)\1", r"<s>\2</s>", content)

	def decode_inline_codeblock(m):
		decoded = base64.b64decode(m.group(1).encode()).decode()

		return f"<span class='inline-codeblock'>{decoded}</span>"

	# Decode and process inline codeblocks
	content = re.sub(r"\x1AI(.*?)\x1AI", decode_inline_codeblock, content)

	# Decode and process links
	if allow_links:
		def decode_link(m):
			encoded_1 = base64.b64decode(m.group(1).encode()).decode()
			encoded_2 = base64.b64decode(m.group(2).encode()).decode()

			return f"<a href='{encoded_2}'>{encoded_1}</a>"

		# Potential bug, may need to change to: '\x1AL(.*?)\|(.*?)\x1AL'
		content = re.sub(r"\x1AL(.*?)\|(.*?)\x1AL", decode_link, content)

	def decode_url(m):
		decoded = base64.b64decode(m.group(1).encode()).decode()

		return f"<a class='link' href='{decoded}'>{decoded}</a>"

	# Decode and process URLs
	content = re.sub("\x1AU(.*?)\x1AU", decode_url, content)

	# Process new lines
	content = content.replace("\n", "<br>")

	def decode_codeblock(m):
		decoded = base64.b64decode(m.group(1).encode()).decode()
		match = re.match(r"^([^`]*?\n)?([^`]+)$", decoded)

		result = html.escape(match.group(2))
		return f"<div class='codeblock'>{result}</div>"

	# Decode and process multiline codeblocks
	content = re.sub("\x1AM(.*?)\x1AM", decode_codeblock, content)

	# Meta mentions (@everyone and @here)
	content = content.replace("@everyone", "<span class='mention'>@everyone</span>")
	content = content.replace("@here", "<span class='mention'>@here</span>")

	# User mentions (<@id> and <@!id>)
	content = re.sub(r"(&lt;@!?(\d+)&gt;)", r"<span class='mention'>\1</span>", content)

	# Channel mentions (<#id>)
	content = re.sub(r"(&lt;#\d+&gt;)", r"<span class='mention'>\1</span>", content)

	# Role mentions (<@&id>)
	content = re.sub(r"(&lt;@&amp;(\d+)&gt;)", r"<span class='mention'>\1</span>", content)

	# Custom emojis (<:name:id>)
	content = re.sub(r"&lt;(:.*?:)(\d*)&gt;", r"<img class='emoji' src='https://cdn.discordapp.com/emojis/\2.png'>", content)

	# Custom animated emojis (<a:name:id>)
	content = re.sub(r"&lt;(a:.*?:)(\d*)&gt;", r"<img class='emoji' src='https://cdn.discordapp.com/emojis/\2.gif'>", content)

	return content

def encode(text):
	as_bytes = text.encode("utf-8")
	as_b64_bytes = base64.b64encode(as_bytes)
	return as_b64_bytes.decode("utf-8")

class Plugin(commands.Cog, name="Message Archiving"):
	"""Should you need to keep a record of messages that were sent but also need to clear them from chat, you can use these commands to create a file and save it for later.

	By default, each archive file is a `.html` file meaning it looks like a web page (i.e. you can open it in your browser). However, you'll also find a big download button near the top that allows you to save a copy of the messages in a plain .txt file as well."""

	def __init__(self, bot):
		self.bot = bot

	@commands.group("archive",
		usage="archive",
		invoke_without_command=True
	)
	async def archive(self, ctx):
		"""The entrypoint to message archiving."""

		raise MissingSubcommand()

	@access_control.require(access_control.Level.MOD)
	@archive.command("here",
		usage="archive here <amount:num>"
	)
	async def archive_here(self, ctx, 
		amount: int
	):
		"""Creates an archive using messages from the current channel."""

		messages = await ctx.channel.history(limit=amount).flatten()
		messages.reverse()

		await self.create_archive(ctx, f"{len(messages)} messages have been archived.", messages)

	@access_control.require(access_control.Level.MOD)
	@archive.command("user",
		usage="archive user <target:user> <amount:num>"
	)
	async def archive_user(self, ctx, 
		target: discord.Member, 
		amount: int
	):
		"""Allows for an archive to be created using messages only sent by the provided user in the current channel."""

		messages = await ctx.channel.history(
			limit=amount,
			check=lambda m: m.author == target
		).flatten()
		messages.reverse()

		await self.create_archive(ctx, f"{len(messages)} messages have been archived.", messages)

	@access_control.require(access_control.Level.MOD)
	@archive.command("channel",
		usage="archive channel <target:channel> <amount:num>"
	)
	async def archive_channel(self, ctx, 
		target: discord.TextChannel, 
		amount: int
	):
		"""Makes an archive with messages from the provided channel rather than the current one."""

		messages = await target.history(limit=amount).flatten()
		messages.reverse()

		await self.create_archive(ctx, f"{len(messages)} messages have been archived.", messages)

	@access_control.require(access_control.Level.MOD)
	@archive.command("bots",
		usage="archive bots <amount:num> [target:channel]"
	)
	async def archive_bots(self, ctx, 
		amount: int, 
		target: discord.TextChannel = None
	):
		"""Archives messages that were only sent by bot accounts in the current or provided channel."""

		target = target or ctx.channel

		messages = await ctx.channel.history(
			limit=amount,
			check=lambda m: m.author.bot
		).flatten()
		messages.reverse()

		await self.create_archive(ctx, f"{len(messages)} messages have been archived.", messages)

	async def create_archive(self, ctx, content, messages):
		async with self.bot.postgres.acquire() as con:
			query = """INSERT INTO message_archives (key) VALUES ($1) RETURNING id;"""

			key = identifier("%A%A%A%A-%A%A%A%A-%A%A%A%A")
			id = await con.fetchval(query, key)

		with open(f"buffer-archive:{key}.html", "w", encoding="utf-8") as file:
			file.write(self.make_html(ctx, id, messages))

		msg = await ctx.success(content,
			file=discord.File(f"buffer-archive:{key}.html",
				filename=f"Archive_{key}.html"
			)
		)
		
		remove(f"buffer-archive:{key}.html")

		async with self.bot.postgres.acquire() as con:
			query = """UPDATE message_archives SET cdn_url = $1 WHERE id = $2;"""

			await con.execute(query, msg.attachments[0].url, id)

	def make_html(self, ctx, id, messages):
		TIMESTAMP_FORMAT = "%d/%m/%y at %H:%M"
		RAW_TIMESTAMP_FORMAT = "%d-%m-%y %H:%M"

		IMAGE_EXTENSIONS = ".png", ".jpg", ".jpeg", ".webp", ".svg"

		message_string = ""
		raw_text = ""

		for m in messages:
			if not m.content and not m.attachments:
				continue

			attachments = ""

			for a in m.attachments:
				if a.url.endswith(IMAGE_EXTENSIONS):
					attachments += f"<a href='{a.url}'><img class='archive-attachment' src='{a.url}'></a>"

				else:
					attachments += f"<div class='archive-attachment-box'><a href='{a.url}' class='archive-attachment-name'>{a.filename}</a><p class='archive-attachment-size'>{bytes_4_humans(a.size)}</p></div>"

			message_string += f"""
				<div class="archive-entry">
					<span class="archive-username">{m.author}</span>
					<span class="archive-timestamp">{m.created_at.strftime(TIMESTAMP_FORMAT)}</span>
					<p>{format_content_html(m.content, True)}</p>
					{attachments}
				</div>
			"""

			raw_text += f"{m.created_at.strftime(RAW_TIMESTAMP_FORMAT)} ({ctx.guild.id} / {m.channel.id} / {m.author.id} / {m.id}) {m.author}: {m.clean_content}\n"

		return f"""
			<!DOCTYPE html>
			<html>
			<head>
				<meta http-equiv="Content-Type" content="text/html;charset=utf-8">
				<link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.3.1/css/all.css" integrity="sha384-mzrmE5qonljUremFsqc01SB46JvROS7bZs3IO2EmfFsd15uHvIt+Y8vEf7N7fWAU" crossorigin="anonymous">
				<meta name="viewport" content="width=device-width,initial-scale=1">
				<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
				<title>Archive #{id}</title>

				<style>
					@import url("https://fonts.googleapis.com/css?family=Nunito:300,400,400i,700");
					body {{background-color: rgb(54, 57, 63);color: white;margin: 50px;font-family: Nunito;}}
					hr {{background-color: rgb(64, 68, 75);height: 1px;border: none;}}
					.archive-attachment {{max-width: 400px;height: auto;border-radius: 4px;}}
					.archive-attachment-size {{margin: 0;font-size: 12px;color: #72767d;font-weight: 300;}}
					.archive-attachment-name {{font-size: 16px;}}
					.link, .archive-attachment-name {{color: rgb(0, 176, 244);text-decoration: none;}}
					.link:hover, .archive-attachment-name:hover {{text-decoration: underline;}}
					.archive-title {{font-size: 70px;display: inline;}}
					.archive-entries {{padding-top: 20px;}}
					.mention {{background-color: rgba(115, 139, 215, 0.1);color: #7289da;}}
					.codeblock, .archive-attachment-box {{max-width: 400px;padding: 10px;margin-bottom: 16px;background-color: rgb(47, 49, 54);border: 1px solid rgb(41, 43, 47);border-radius: 5px;color: rgb(185, 187, 190);}}
					.codeblock-inline {{font-family: Menlo, Consolas, Monaco, monospace;font-size: 14px;line-height: 16px;padding: 2px;border-radius: 3px;background-color: #23272A;}}
					.emoji {{height: 25px;width: 25px;vertical-align:middle;}}
					p, .archive-username {{font-size: 16px;}}
					p, .codeblock {{white-space: pre-wrap;vertical-align:middle;}}
					.archive-username {{color: #7289DA;}}
					.archive-timestamp {{font-size: 12px;color: rgb(114, 118, 125);margin-left: 10px;padding-bottom: 20px;}}
					.archive-download {{font-size: 35px;color: #7289DA;display: inline;margin-left: 10px;}}
					@media screen and (max-width: 480px) {{.archive-attachment {{max-width: calc(100vw - 50px) !important;}}.embed-image {{max-width: calc(100vw - 124px) !important;}}}}
				</style>
			</head>
			<body>
				<h2 class="archive-title">Archive #{id}</h2>
				<a class="archive-download" id="download-button" href="data:text/plain;charset=utf-8;base64,{encode(raw_text)}" download="Archive_{id}.txt">
					<i class="fas fa-download"></i>
				</a>
				<p class="archive-timestamp">Created by {ctx.author} at {datetime.utcnow().strftime(TIMESTAMP_FORMAT)}</p>
				<hr>

				<div class="archive-entries">
					{message_string}
				</div>
			</body>
			</html>
		"""

def setup(bot):
	bot.add_cog(Plugin(bot))