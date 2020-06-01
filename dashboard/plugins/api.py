# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from typing import Union


# --------------------
# Builtin dependencies
# --------------------
from datetime import datetime
from json import dumps

# ------------------------
# Third-party dependencies
# ------------------------
from flask import jsonify, request, render_template

# -------------------------
# Local extension libraries
# -------------------------
import util.utilities as utils

from util import console
from util.blueprints import Archive
from util.constants import app, config, postgres


BASE = "/api"

@app.route(rule=BASE + "/archive",
           methods=["POST"])
def upload_archive():
    """Allows an authorised user to upload a user's archived messages to a text file.
    
    Since this a POST route that could be abused, an Authorisation token
    is required for the user to be able to upload an archive."""

    auth_token = request.headers.get("Authorization", "missing_token")

    if auth_token != config.token:
        return utils.respond(code=403,
                             msg="Invalid or missing appropriate API authorisation token.")

    if request.json is None:
        return utils.respond(code=422,
                             msg="Invalid MIMEtype, it should be application/json.")

    transcript = request.json.get("messages", [])
    
    if transcript is None:
        return utils.respond(code=422,
                             msg="Invalid or missing transcript data.")

    author_id = utils.intable(string=request.json.get("author_id", 0))
    guild_id = utils.intable(string=request.json.get("guild_id", 0))

    # =======================================================
    # we don't actually need to do any interpreting here this 
    # is because archives are stored as JSON in Postgres
    # =======================================================
    with postgres.cursor() as con:
        query = """INSERT INTO archives (key, author_id, guild_id, data, created_at)
                   VALUES (%(key)s, %(author_id)s, %(guild_id)s, %(data)s, %(created_at)s);"""

        key = utils.gen_id()
        
        con.execute(query,
                    dict(key=key,
                         author_id=author_id,
                         guild_id=guild_id,
                         data=dumps(obj=transcript),
                         created_at=datetime.utcnow()))
        postgres.commit()

    console.debug(text=f"{author_id} uploaded an archive with key {key}")
    return utils.respond(key=key)

@app.route(rule=BASE + "/archive",
           defaults=dict(key=None))
@app.route(rule=BASE + "/archive/<key>")
def get_archive(key: Union[str, None]):
    """Handles retrival of a previously created archive.
    
    This may also be read as a webpage by providing ?view=webpage, defaults to file."""

    if key is None:
        return utils.respond(code=422,
                             msg="Missing archive ID.")

    view_type = request.args.get("view", "file")

    with postgres.cursor() as con:
        query = """SELECT id, key, data, author_id, guild_id, created_at
                   FROM archives
                   WHERE key = %(key)s;"""

        con.execute(query,
                    dict(key=key))

        found_archive = con.fetchone()

        if found_archive is None:
            if view_type == "webpage":
                return render_template(template_name_or_list="archive.html",
                                       key=key,
                                       id=0,
                                       found=False), 404

            return utils.respond(code=404,
                                 msg=f"No archive was found with the key: {key}")

    archive = Archive(payload={
        "id": found_archive[0],
        "key": found_archive[1],
        "messages": found_archive[2],
        "author_id": found_archive[3],
        "guild_id": found_archive[4],
        "created_at": found_archive[5]
    })

    if view_type.lower() == "webpage":
        return render_template(template_name_or_list="archive.html",
                               
                               messages=archive.messages,
                               author_id=archive.author_id,
                               guild_id=archive.guild_id,
                               created_at=archive.created_at(fancy=True),
                               id=archive.id,
                               key=archive.key,

                               download_text=archive.raw_text,
                               found=True)

    if view_type.lower() == "json":
        return jsonify(archive.raw_json)

    return "<br>".join(archive.raw_text)