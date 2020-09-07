import ext.state as state

from core import Core, version_info
from psycopg2 import connect


VERSION = version_info(
	name="cweb",
	major=1,
	minor=0,
	patch=0,
	release="stable"
)

app = state.app = Core()

try:
	db = app.db = connect(app.settings.get("postgres"))
	db.set_session(autocommit=True)

	with db.cursor() as con:
		queries = """CREATE TABLE IF NOT EXISTS guild_configs (id BIGINT UNIQUE, config TEXT);""",

		for query in queries:
			con.execute(query)

	app.log.info("Connected to PostgreSQL server.")

except:
	app.log.fatal("Failed to connect to PostgreSQL server.",
		exc_info=True
	)
	quit()

app.log.info("Running {0.name} v{0.major}.{0.minor}.{0.patch}-{0.release}".format(VERSION))

import plugins.api, plugins.ui

app.boot()