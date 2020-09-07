from functools import wraps

from ext.exceptions import RequiresAuth
from ext.models import OAuth2Handler
from ext.state import app

def require_auth(func):
	@wraps(func)
	def wrapper(*args, **kwargs):
		discord = OAuth2Handler.from_token()
		if discord is None:
			raise RequiresAuth

		return func(discord, *args, **kwargs)

	return wrapper

def require_guild(discord, gid):
	guild = None
	for g in discord.guilds:
		if g.get("id") == gid:
			perms = int(g.get("permissions_new"))

			if (perms & 8 == 8) or (perms & 32 == 32):
				guild = g
				break

	return guild