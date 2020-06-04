# Copyright (C) Mila Software Group 2018-2020
# -------------------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from typing import Any, Callable, Dict, List


# --------------------
# Builtin dependencies
# --------------------
from contextlib import redirect_stdout
from importlib import import_module
from io import StringIO
from textwrap import indent
from time import perf_counter
from traceback import format_tb

# ------------------------
# Third-party dependencies
# ------------------------
import discord

from discord.ext import commands, tasks

# -------------------------
# Local extension libraries
# -------------------------
from .helpers import clean_io, format_error, get_syntax_error, strip_blocks, strip_token


class Evaluator(commands.Cog, name="Evaluator Command"):
    """This plugin adds an evaluator command to the main bot."""

    def __init__(self,
                 bot: commands.Bot,
                 *args, **kwargs):
        self.last_result = None

        self.bot = bot

        self.scan_for_token = kwargs.pop("scan_for_token", True)
        self.attrs = {
            "name": "eval",
            "usage": "eval <code:text>",
            "aliases": ["evaluate", "exec", "execute"],
            "checks": [lambda ctx: self.bot.is_owner(user=ctx.author)],
            "extra_attrs": {},
            "imports": [],
            "vars": {}
        }
        self.attrs.update(kwargs.pop("config", {}))

        eval_command = commands.Command(func=self.command_callback,
                                        name=self.attrs["name"],
                                        usage=self.attrs["usage"],
                                        aliases=self.attrs["aliases"],
                                        cog=self,
                                        **self.attrs["extra_attrs"])

        self.bot.add_command(command=eval_command)

        for check in self.attrs["checks"]:
            eval_command.add_check(func=check)

    @commands.bot_has_permissions(send_messages=True)
    async def command_callback(self,
                               ctx: commands.Context,
                               *, code: str):
        """Evaluates the provided text and returns a clean and formatted result."""

        start_timer = perf_counter()

        for import_path in self.attrs["imports"]:
            import_module(import_path)

        ENV_VARS = {
            "ctx": ctx,
            "guild": ctx.guild,
            "channel": ctx.channel,
            "message": ctx.message,
            "author": ctx.author,

            "bot": self.bot,
            "self": self,
            "_": self.last_result,

            "discord": discord,
            "commands": commands,
            "tasks": tasks
        }

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # update environment variables with globals and configured vars
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        ENV_VARS.update(globals())
        ENV_VARS.update(self.attrs["vars"])

        code = strip_blocks(string=code)
        stdout = StringIO()
        
        to_compile = f"async def func():\n{indent(text=code, prefix='    ')}"
        
        try:
            exec(to_compile, ENV_VARS)

        except SyntaxError as error:
            return self.bot.dispatch(event_name="eval_error",
                                     ctx=ctx,
                                     code=code,
                                     error=error,
                                     took=perf_counter() - start_timer)

        func = ENV_VARS["func"]

        try:
            with redirect_stdout(stdout):
                result = await func()
        
        except Exception as error:
            return self.bot.dispatch(event_name="eval_error",
                                     ctx=ctx,
                                     code=code,
                                     error=error,
                                     took=perf_counter() - start_timer)
        
        self.last_result = result
        self.bot.dispatch(event_name="eval_success",
                          ctx=ctx,
                          code=code,
                          result=strip_token(string=result),
                          took=perf_counter() - start_timer)

    @commands.Cog.listener()
    async def on_message(self,
                         message: discord.Message):
        """This runs a scan on every message sent by the bot to see if it can find the token.
        
        If found, the token_breach event is sent and the message is deleted by default."""

        if not self.scan_for_token:
            return

        token = self.bot.http.token

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # the str() call here avoids errors if message.content == None
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        if token in str(message.content):
            return self.bot.dispatch(event_name="token_breach",
                                     message=message)

        for embed in message.embeds:
            for search_query in (embed.title, embed.description, 
                                 embed.footer.text if hasattr(embed.footer, "text") else "", 
                                 embed.footer.icon_url if hasattr(embed.footer, "icon_url") else "", 
                                 embed.author.name if hasattr(embed.author, "name") else "", 
                                 embed.author.icon_url if hasattr(embed.author, "icon_url") else "", 
                                 *[field.name for field in embed.fields], 
                                 *[field.value for field in embed.fields]):
                if search_query is discord.Embed.Empty:
                    continue
                
                if token in search_query:
                    return self.bot.dispatch(event_name="token_breach",
                                             message=message)

    @commands.Cog.listener()
    async def on_token_breach(self,
                              message: discord.Message):
        """This triggers when the bot detects a message it has sent containing the token.
        
        By default, this deletes the message and sends a DM to each bot owner.
        To override this functionality, just create a new listener with the same name."""

        if len(self.bot.extra_events.get("on_token_breach", [])) > 1:
            return

        await message.delete()

        if self.bot.owner_id and not self.bot.owner_ids:
            owner = await self.bot.fetch_user(user_id=self.bot.owner_id)#

            try:
                return await owner.send(content=f":rotating_light: **TOKEN BREACH DETECTED** :rotating_light:\n\n{message.guild} ({message.guild.id}) > {message.channel.mention} ({message.channel.id})\n\n**ACTION TAKEN:** Message deleted.\n\n**SUGGESTED FURTHER ACTION:** Reset the token immediately.")

            except:
                return

        for owner_id in self.bot.owner_ids:
            owner = await self.bot.fetch_user(user_id=owner_id)

            try:
                await owner.send(content=f":rotating_light: **TOKEN BREACH DETECTED** :rotating_light:\n\n{message.guild} ({message.guild.id}) > {message.channel.mention} ({message.channel.id})\n\n**ACTION TAKEN:** Message deleted.\n\n**SUGGESTED FURTHER ACTION:** Reset the token immediately.")

            except:
                pass

    @commands.Cog.listener()
    async def on_eval_success(self,
                              ctx: commands.Context,
                              code: str,
                              result: Any,
                              took: float):
        """This is the default handler for evaluation successions.
        
        To switch to your own handler, just create a listener with the same name."""

        if len(self.bot.extra_events.get("on_eval_success", [])) > 1:
            return

        try:
            await ctx.message.add_reaction("✅")
        
        except:
            pass

        await ctx.send(embed=discord.Embed(colour=0x43b581,
                                           title="Evaluation Result",
                                           description=f"Evaluated in {round(took * 1000, 2)} milliseconds.") \
                                    .add_field(name=":inbox_tray: Input",
                                               value=f"```py\n{clean_io(string=code)}```",
                                               inline=False) \
                                    .add_field(name=":outbox_tray: Output",
                                               value=f"```py\n{clean_io(string=result)}```",
                                               inline=False) \
                                    .add_field(name=":bookmark: Result type",
                                               value=f"```py\n{result.__class__.__name__}```",
                                               inline=False))

    @commands.Cog.listener()
    async def on_eval_error(self,
                            ctx: commands.Context,
                            code: str,
                            error: Any,
                            took: float):
        """This is the default handler for eval errors.
        
        To switch to your own handler, just create a new listener with the same event name."""

        if len(self.bot.extra_events.get("on_eval_error", [])) > 1:
            return

        try:
            await ctx.message.add_reaction("❌")
        
        except:
            pass

        if isinstance(error, SyntaxError):
            traceback = get_syntax_error(exception=error)

        else:
            traceback = format_error(error=error)

        await ctx.send(embed=discord.Embed(colour=0xf04947,
                                           title="Evaluation Error",
                                           description=f"Evaluated in {round(took * 1000, 2)} milliseconds.") \
                                    .add_field(name=":inbox_tray: Input",
                                               value=f"```py\n{clean_io(string=code)}```",
                                               inline=False) \
                                    .add_field(name=":outbox_tray: Output",
                                               value=f"```py\n{clean_io(string=traceback)}```",
                                               inline=False) \
                                    .add_field(name=":bookmark: Exception type",
                                               value=f"```py\n{error.__class__.__name__}```",
                                               inline=False))