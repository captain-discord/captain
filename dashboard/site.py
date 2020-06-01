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
from typing import Optional


# -----------------
# Builtin libraries
# -----------------
from atexit import register
from datetime import datetime
from os import _exit, listdir

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from custos import blueprint

from util import console, constants
from util.constants import config

# ------------------------
# Third-party dependencies
# ------------------------
try:
    from attrdict import AttrDict
    from flask import Flask
    from gevent.pywsgi import WSGIServer
    from pyfiglet import FontNotFound, print_figlet
    from psycopg2 import connect

except ImportError as error:
    console.fatal(text=f"{error.name} dependency is missing.")
    
    _exit(status=2)

constants.app = Flask(import_name="Website")

class Website(blueprint):
    def on_exit(self):
        """This runs some code before we quietly close down."""
        
        console.fatal(text="Shutting down...")
        self.print_fig(stop=True)

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

    def postgres_init(self):
        """Initialises the connection to the PostgreSQL server."""

        constants.postgres = connect(dsn="user={pg.user} password={pg.password} host={pg.host} port={pg.port} dbname={pg.database}".format(pg=config.postgres))
        console.info(text="Connected to Postgres server at: {pg.user}@{pg.host}/{pg.database}".format(pg=config.postgres))

        # =================================
        # Create the required schema tables
        # =================================
        with constants.postgres.cursor() as con:
            queries = ("""CREATE TABLE IF NOT EXISTS archives (id SERIAL PRIMARY KEY, key VARCHAR(19), author_id BIGINT, guild_id BIGINT, data TEXT, created_at TIMESTAMP);""",)

            for query in queries:
                con.execute(query)
                constants.postgres.commit()

    def boot(self,
             host: Optional[str] = "127.0.0.1",
             port: Optional[int] = 5000):
        """This runs any necessary pre-init code and then begins the server session."""
        
        # =====================
        # Register exit handler
        # =====================
        register(self.on_exit)

        # ==============================
        # Initialise Postgres connection
        # ==============================
        try:
            self.postgres_init()

        except Exception as error:
            console.fatal(text="Failed to connect to Postgres at: {pg.user}@{pg.host}/{pg.database}\n\n{error}".format(pg=config.postgres,
                                                                                                                       error=error))
            _exit(status=2)

        # ==================
        # Initialise plugins
        # ==================
        for plugin in (file[:-3] for file in listdir(path="plugins") if file.endswith(".py")):
            try:
                __import__(name=f"plugins.{plugin}")
                console.debug(text=f"{plugin} plugin successfully booted.")

            except Exception as error:
                console.error(text=f"{plugin} plugin failed to boot.\n\n{error}\n\n{error.__cause__}")

                _exit(status=2)

        # =============================
        # Start server and print FIGlet
        # =============================
        console.info(text=f"Server started at: http://{host}:{port}")
        self.print_fig()


if __name__ == "__main__":
    Website().boot(host=config.server.host,
                   port=config.server.port)

    WSGIServer((config.server.host, config.server.port), constants.app, 
                log=None).serve_forever()