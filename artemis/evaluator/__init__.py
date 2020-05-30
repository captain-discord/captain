# Copyright (C) Mila Software Group 2018-2020
# -------------------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from discord.ext import commands


# -------------------------
# Local extension libraries
# -------------------------
from .evaluator import Evaluator
from .helpers import __register_helper, clean_io, format_error, get_syntax_error, strip_blocks, strip_token


def register(bot: commands.Bot,
             *args, **kwargs):
    """Registers the evaluator cog with the bot."""

    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # these should not be called outside of this function
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    __register_helper(bot=bot)
    
    bot.add_cog(cog=Evaluator(bot=bot,
                              *args, **kwargs))