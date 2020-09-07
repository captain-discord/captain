from functools import wraps
from yaml import safe_load

from ext.exceptions import RequiresAuth
from ext.models import OAuth2Handler
from ext.state import app


class WebAccessEnum:
	EDITOR = 0
	VIEWER = 1

def require_auth(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		discord = OAuth2Handler.from_token()
		if discord is None:
			raise RequiresAuth

		return func(discord, *args, **kwargs)

	return wrapper

def require_guild(discord, gid, require_edit=False):
	for g in discord.guilds:
		if g.get("id") == gid:
			perms = int(g.get("permissions_new"))

			if (perms & 8 == 8) or (perms & 32 == 32):
				return g

			with app.db.cursor() as con:
				query = """SELECT config FROM guild_configs
						   WHERE id = %(gid)s;"""

				con.execute(query, dict(gid=gid))
				result = con.fetchone()
				if result is None:
					return

				result = result[0]

				try:
					web_config = safe_load(result).get("web", {})
					
				except:
					web_config = {}

				web_access = web_config.get(int(discord.user.get("id")))
				if web_access is None:
					return

				if require_edit:
					return g if web_access == WebAccessEnum.EDITOR else None

				return g if web_access in (WebAccessEnum.EDITOR, WebAccessEnum.VIEWER) else None