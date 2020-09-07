import os

from flask import abort, jsonify, session, redirect, render_template, request

from ext.exceptions import RequiresAuth
from ext.models import CLIENT_ID, OAuth2Handler
from ext.state import app
from ext.utils import require_auth, require_guild

BASE = "/dash"


@app.route("/")
def index():
	discord = OAuth2Handler.from_token()
	if discord is not None:
		return redirect("/dash")

	return render_template("index.html")

@app.route(BASE)
@require_auth
def dash(discord):
	available_guilds = []
	for guild in discord.guilds:
		g = require_guild(discord, guild.get("id"))
		if g is not None:
			available_guilds.append(g)

	return render_template("dash/guilds.html",
		discord=discord,
		guilds=available_guilds
	)

@app.route(BASE + "/<gid>")
@require_auth
def guild_overview(discord, gid):
	guild = require_guild(discord, gid)
	if guild is None:
		return abort(403)

	info = discord.get_guild(gid)
	if info is None:
		return redirect(f"/api/invite?gid={gid}")

	return render_template("dash/overview.html",
		info=info,
		id=gid
	)

@app.route(BASE + "/<gid>/config")
@require_auth
def edit_config(discord, gid):
	guild = require_guild(discord, gid)
	if guild is None:
		return abort(403)
	
	with app.db.cursor() as con:
		query = """SELECT config FROM guild_configs
				   WHERE id = %(guild_id)s;"""

		con.execute(query, dict(guild_id=guild.get("id")))
		result = con.fetchone()
	
	return render_template("dash/config.html",
		id=gid,
		config=result[0] if result is not None else ""
	)

@app.route(BASE + "/<gid>/infractions")
@require_auth
def infractions(discord, gid):
	guild = require_guild(discord, gid)
	if guild is None:
		return abort(403)

	with app.db.cursor() as con:
		query = """SELECT id, actor_id, target_id, type_id, created_at, reason FROM infractions
				   WHERE guild_id = %(guild_id)s;"""

		con.execute(query, dict(guild_id=guild.get("id")))
		result = con.fetchall()
	
	return render_template("dash/infractions.html",
		id=gid,
		infractions=result
	)

@app.route(BASE + "/<gid>/leaderboard")
@require_auth
def leaderboard(discord, gid):
	guild = require_guild(discord, gid)
	if guild is None:
		return abort(403)
	
	return render_template("dash/leaderboard.html",
		id=gid
	)

@app.errorhandler(RequiresAuth)
def handle_unauthorised(e):
	return redirect("/api/login")