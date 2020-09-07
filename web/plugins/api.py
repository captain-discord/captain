import os

import ext.state as state

from flask import jsonify, redirect, request, session
from yaml import safe_load

from ext.models import CLIENT_ID, OAuth2Handler
from ext.state import app
from ext.utils import require_auth, require_guild

BASE = "/api"
INVITE_BASE = "https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions={perms}&scope=bot"


@app.route(BASE + "/login")
def login():
	SCOPE = "identify guilds"

	discord = OAuth2Handler(scope=SCOPE.split(" "))
	return redirect(discord.auth_url)

@app.route(BASE + "/logout")
@require_auth
def logout(discord):
	del session["oauth2_token"]
	del session["oauth2_state"]
	del session["oauth2_user"]
	del state.oauth_cache[discord.user.get("id")]

	return redirect("/")

@app.route(BASE + "/invite")
def invite():
	gid = request.args.get("gid")
	perms = request.args.get("perms", 8)

	if gid is None:
		return redirect(INVITE_BASE.format(
			client_id=CLIENT_ID,
			perms=perms
		))

	return redirect(INVITE_BASE.format(
		client_id=CLIENT_ID,
		perms=perms
	) + f"&guild_id={gid}")

@app.route(BASE + "/<gid>/config",
	methods=["PUT", "POST"]
)
@require_auth
def update_config(discord, gid):
	if not request.is_json:
		return jsonify({
			"code": 415,
			"message": "Content-Type must be application/json"
		}), 415

	guild = require_guild(discord, gid, True)
	if guild is None:
		return jsonify({
			"code": 403,
			"message": "You don't have permission to change the guild's config or the guild doesn't exist."
		}), 403

	updated_config = request.json.get("newConfig")

	try:
		safe_load(updated_config)

	except:
		return jsonify({
			"code": 400,
			"message": "Malformed yaml config."
		})

	with app.db.cursor() as con:
		query = """INSERT INTO guild_configs (id, config)
				   VALUES (%(id)s, %(config)s)
				   ON CONFLICT (id) DO UPDATE
				   SET config = %(config)s
				   WHERE guild_configs.id = %(id)s;"""

		con.execute(query, dict(
			id=gid, 
			config=updated_config
		))

		return jsonify({
			"code": 200,
			"message": "Configuration successfully updated."
		})

@app.route(BASE + "/callback")
def callback():
	discord = OAuth2Handler.from_state()
	discord.handle_callback()

	return redirect("/dash")