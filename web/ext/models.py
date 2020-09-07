import requests, os

import ext.state as state

from flask import session, request
from requests_oauthlib import OAuth2Session

from ext.state import app


BASE = "/api"

CLIENT_ID = app.settings.get("oauth2", {}).get("client_id")
CLIENT_SECRET = app.settings.get("oauth2", {}).get("client_secret")
REDIRECT_URI = app.settings.get("oauth2", {}).get("redirect_uri") + "/api/callback"
BOT_TOKEN = "Bot " + app.settings.get("oauth2", {}).get("bot_token")

API_BASE_URL = "https://discord.com/api"
AUTHORIZATION_BASE_URL = API_BASE_URL + "/oauth2/authorize"
TOKEN_URL = API_BASE_URL + "/oauth2/token"

if REDIRECT_URI.startswith("http://"):
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "true"


state.oauth_cache = {}

class OAuth2Handler(OAuth2Session):
	def __init__(self, token=None, state=None, scope=None):
		super().__init__(
			client_id=CLIENT_ID,
			token=token,
			state=state,
			scope=scope,
			redirect_uri=REDIRECT_URI,
			auto_refresh_kwargs={
				"client_id": CLIENT_ID,
				"client_secret": CLIENT_SECRET,
			},
			auto_refresh_url=TOKEN_URL,
			token_updater=self.updater
		)

	@classmethod
	def from_token(cls):
		token = session.get("oauth2_token")
		if token is None:
			return None

		return cls(token=token)

	@classmethod
	def from_state(cls):
		state = session.get("oauth2_state")
		if state is None:
			return None

		return cls(state=state)

	def updater(self, token):
		session["oauth2_token"] = token
		return token

	@property
	def auth_url(self):
		url, state = self.authorization_url(AUTHORIZATION_BASE_URL)
		session["oauth2_state"] = state

		return url

	def handle_callback(self):
		token = self.updater(self.fetch_token(TOKEN_URL,
			client_secret=CLIENT_SECRET,
			authorization_response=request.url if request.is_secure and request.url.startswith("http://") else "https://" + request.url[7:]
		))
		return token

	@property
	def user(self):
		if session.get("oauth2_user") is not None:
			return session["oauth2_user"]

		result = session["oauth2_user"] = self.get(API_BASE_URL + "/users/@me").json()
		return result

	@property
	def guilds(self):
		if self.user.get("id") in state.oauth_cache.keys():
			return state.oauth_cache[self.user.get("id")]

		result = state.oauth_cache[self.user.get("id")] = self.get(API_BASE_URL + "/users/@me/guilds").json()
		return result

	def get_guild(self, id, with_counts=True):
		id = int(id)

		if id in state.guild_cache.keys():
			return state.guild_cache[id]

		url = API_BASE_URL + f"/guilds/{id}"

		if with_counts:
			url += "?with_counts=true"

		result = requests.get(url,
			headers={
				"Authorization": BOT_TOKEN
			}
		).json()
		
		if result.get("id") is not None:
			state.guild_cache[id] = result
			return result

		return None


# class User:
# 	def __init__(self, payload):
# 		self.raw = payload

# 		self.name = payload.pop("username")
# 		self.discriminator = int(payload.pop("discriminator"))
# 		self.id = int(payload.pop("id"))

# 		self.avatar = payload.pop("avatar")

# 	def __str__(self):
# 		return f"{self.name}#{self.discriminator}"

# 	def __repr__(self):
# 		return "<User name='{0.name}' discriminator={0.discriminator} id={0.id} avatar='{0.avatar}' avatar_url='{0.avatar_url}'>".format(self)
	
# 	@property
# 	def avatar_url(self):
# 		if self.avatar is None:
# 			return None

# 		if self.avatar.startswith("a_"):
# 			return ANIMATED_AVATAR_BASE_URL.format(
# 				id=self.id,
# 				hash=self.avatar
# 			)	

# 		return AVATAR_BASE_URL.format(
# 			id=self.id,
# 			hash=self.avatar
# 		)


# class Guild:
# 	def __init__(self, payload):
# 		self.raw = payload

# 		self.name = payload.pop("name")
# 		self.id = int(payload.pop("id"))

# 		self.permissions = payload.pop("permissions", 0)
# 		self.owner = payload.pop("owner")
# 		self.icon = payload.pop("icon")

# 	def __repr__(self):
# 		return "<Guild name='{0.name}' id={0.id} permissions={0.permissions} owner={0.owner} icon='{0.icon}' icon_url='{0.icon_url}'>".format(self)

# 	@property
# 	def icon_url(self):
# 		if self.icon is None:
# 			return None

# 		if self.icon.startswith("a_"):
# 			return ANIMATED_ICON_BASE_URL.format(
# 				id=self.id,
# 				hash=self.icon
# 			)	

# 		return ICON_BASE_URL.format(
# 			id=self.id,
# 			hash=self.icon
# 		)