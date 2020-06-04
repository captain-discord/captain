# Copyright (C) Mila Software Group 2018-2020
# -------------------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
import discord

from discord.ext import commands
from typing import Any, Optional


# --------------------
# Builtin dependencies
# --------------------
from traceback import format_tb


BOT = None

def __register_helper(bot: commands.Bot):
    """Do NOT call this function yourself."""

    global BOT
    BOT = bot

def strip_token(string: str,
                replace_with: Optional[str] = "redacted") -> str:
    """This replaces any occurence of the bot's token with the replace text."""

    if not isinstance(string, str):
        return string

    if BOT is None:
        return string

    return string.replace(BOT.http.token, replace_with)

def strip_blocks(string: str) -> str:
    """Strips code blocks from the body."""

    if string.startswith("```") and string.endswith("```"):
        return "\n".join(string.split("\n")[1:-1])
    
    return string.strip("` \n")

def get_syntax_error(exception: Exception):
    if exception.text is None:
        return f"{exception.__class__.__name__}: {exception}"

    return f"{exception.text[4:]}{'^':>{exception.offset}}\n{exception.__class__.__name__}: {exception}"

def format_error(error: Any):
    """Takes an error and formats it into a neat error string."""

    traceback = "\n".join((line[2:] if line.startswith("  ") else line) for line in format_tb(tb=error.__traceback__)[2:]).rstrip("\n")

    return f"{traceback}\n\n{error}"

def clean_io(string: Any):
    """Cleans up the input/output string including markdown escaping and token redacting."""

    if not isinstance(string, str):
        return string

    return strip_blocks(string=strip_token(string=string))