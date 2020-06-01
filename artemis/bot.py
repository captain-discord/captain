# Copyright (C) JackTEK 2018-2020
# -------------------------------
# This is the main file, only ever run this file.

# Introduction to commenting
# --------------------------
# All comments within these files will be surrounded by lines to make them stand out.

# = top level/vague overview
# - lower level/more specific explanation
# ~ notes or explanation of a small amount of code

# Incomplete or WIP sections of code will also use the following formatting:
# ! = something here is being or has been deprecated
# ? = query in place about something
# * = version note
# TODO = details something that needs to be done
# REF = references something to previous comment
# TEMPORARY = indicates that this line or lines of code is temporary

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from typing import Callable, List, Optional, Union


# -----------------
# Builtin libraries
# -----------------
import atexit, os, sys

from asyncio import all_tasks, get_event_loop
from datetime import datetime
from traceback import format_tb

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from custos import blueprint

from util import console, constants
from util.blueprints import Emoji, Plugin, Presence
from util.constants import cache, config

# ------------------------
# Third-party dependencies
# ------------------------
try:
    import discord, tabulate, termcolor

    from attrdict import AttrDict
    from asyncpg import create_pool
    from discord.ext import commands
    from redis import exceptions, Redis
    from pyfiglet import FontNotFound, print_figlet
    from yaml import safe_load

except ImportError as error:
    console.fatal(text=f"{error.name} failed to import.\n\n{error}")
    os._exit(status=2)


class Artemis(blueprint, commands.Bot):
    def on_exit(self):
        """This runs some code before we quietly close down."""
        
        console.fatal(text="Shutting down...")
        self.print_fig(stop=True)

    def shutdown(self):
        """This calmly and quietly closes the running event loops and any tasks.
        
        This exists with a status code of 2."""

        # ================================
        # Cancel all running asyncio tasks
        # ================================
        try:
            for task in all_tasks():
                try: 
                    task.cancel()

                except: 
                    continue

        except RuntimeError: 
            pass
        
        # =======================
        # Disconnect from Discord
        # =======================
        try:
            self.loop.run_until_complete(self.logout())
            self.loop.stop()
            self.loop.close()
        
        except: 
            pass

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # atexit doesn't run its register if we exit with a status code of 2 
        # (intentional exit) so we're going to have to call the on_exit function
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.on_exit()
        os._exit(status=2)

    def print_fig(self,
                  stop: Optional[bool] = False):
        """Prints either the startup or shutdown Figlet depending on the value of stop."""

        local_config = config.figlet

        try:
            print_figlet(text=local_config.stop if stop else local_config.start,
                         width=local_config.width,
                         font=local_config.font)

        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # the configured font doesn't exist, so we force a change 
        # to the loaded config and send a warning message to the console 
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        except FontNotFound:
            console.warn(text=f"{local_config.font} font not found, fixing.")
            
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            # attrdict creates shallow copies internally when we access it
            # using the attribute syntax, so we have to use the key syntax
            # to be able to edit the attributes
            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
            config["figlet"]["font"] = "standard"

            print_figlet(text=local_config.stop if stop else local_config.start,
                         width=local_config.width,
                         font="standard")

    async def _prefix_callable(self,
                               artemis: commands.Bot,
                               message: discord.Message) -> Union[Callable, List]:
        """A callable that returns an appropriate prefix."""

        local_config = config.prefix

        prefixes = list(local_config.aliases)
        prefixes.insert(0, local_config.default)
        
        if local_config.mention:
            if isinstance(prefixes, str):
                prefixes = prefixes,

            return commands.when_mentioned_or(*prefixes)(artemis, message)

        return prefixes

    def __init__(self):
        super().__init__(command_prefix=self._prefix_callable,
                         owner_ids=config.owners,
                         max_messages=config.message_cache)

    async def postgres_init(self):
        """Initialises the connection to the PostgreSQL server."""

        constants.postgres = await create_pool(dsn="postgresql://{pg.user}:{pg.password}@{pg.host}:{pg.port}/{pg.database}".format(pg=config.postgres))
        console.info(text="Connected to Postgres server at: {pg.user}@{pg.host}/{pg.database}".format(pg=config.postgres))

        # =================================
        # Create the required schema tables
        # =================================
        async with constants.postgres.acquire() as con:
            queries = ("""CREATE TABLE IF NOT EXISTS infractions (id SERIAL PRIMARY KEY, case_id SMALLINT, guild_id BIGINT, actor_id BIGINT, target_id BIGINT, type_id BIGINT, reason TEXT, timestamp TIMESTAMP);""",
                       """CREATE TABLE IF NOT EXISTS timers (id SERIAL PRIMARY KEY, event TEXT, expire_at TIMESTAMP, extras TEXT);""")

            for query in queries:
                await con.execute(query)

    def boot(self):
        """This runs any necessary pre-init code and then begins the gateway connection."""

        # =============================
        # Prepare helpers and internals
        # =============================
        atexit.register(self.on_exit)
        self.remove_command(name="help")
        
        # ==============================
        # Initialise Postgres connection
        # ==============================
        try:
            self.loop.run_until_complete(self.postgres_init())

        except Exception as error:
            console.fatal(text="Failed to connect to Postgres at: {pg.user}@{pg.host}/{pg.database}\n\n{error}".format(pg=config.postgres,
                                                                                                                       error=error))
            self.shutdown()

        # ===========================
        # Initialise Redis connection
        # ===========================
        try:
            constants.redis = Redis(host=config.redis.host,
                                    port=config.redis.port,
                                    password=config.redis.password,
                                    db=config.redis.database)
            constants.redis.ping()

            console.info(text="Connected to Redis server at: {r.host}:{r.port}/{r.database}".format(r=config.redis))

        except exceptions.ConnectionError as error:
            console.fatal(text="Failed to connect to Redis at: {r.host}:{r.port}/{r.database}\n\n{error}".format(r=config.redis,
                                                                                                                 error=error))
            self.shutdown()

        # ==========================
        # Populate some of the cache
        # ==========================
        cache.presence = Presence(**config.presence)
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # by placing this here, we avoid complications with the value of emojis from
        # within plugins, we also avoid the alternative which is load it in constants.py
        # which would cause a cyclic import error because we need the Emoji blueprint
        # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        constants.emojis = AttrDict({key: Emoji(**value) for key, value in safe_load(open(file="emojis.yml")).items()})

        # ===============================
        # Load files in plugins directory
        # ===============================
        cache["plugins"] = [Plugin(file_name=plugin) for plugin in os.listdir(path="plugins") if plugin.endswith(".py")]
        console.debug(text=f"Attempting to load {len(cache.plugins)} plugins.")

        for plugin in cache.plugins:
            if not plugin.enabled:
                console.warn(text=f"{plugin.name} plugin is disabled, skipping.")
                continue

            try:
                self.load_extension(name=plugin.path)
                console.debug(text=f"{plugin.name} plugin successfully loaded.")

                plugin.loaded = True

            except commands.ExtensionFailed as error:
                traceback = "\n".join(format_tb(tb=error.original.__traceback__))
                console.warn(text=f"{plugin.name} plugin failed to load.\n\n{traceback}\n\n{error.__cause__}")

        loaded_plugins = utils.all(iterable=cache.plugins, 
                                   condition=lambda plugin: plugin.loaded)
        console.info(text=f"{len(loaded_plugins)} / {len(cache.plugins)} plugins have booted.")

        # =============================
        # Connect to Discord's gateways
        # =============================
        try:
            self.run(config.token)
        
        except (RuntimeError, KeyboardInterrupt):
            self.shutdown()


if __name__ == "__main__":
    Artemis().boot()