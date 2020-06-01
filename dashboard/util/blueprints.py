# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from typing import Optional


# --------------------
# Builtin dependencies
# --------------------
from datetime import datetime
from json import loads

# ------------------------
# Third-party dependencies
# ------------------------
from attrdict import AttrDict

# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint

from .utilities import intable


class Archive(blueprint):
    def __init__(self,
                 payload: dict):
        self.raw_json = payload
        self.messages = [Message(json_object=message) for message in loads(payload.pop("messages", []))]

        self.guild_id = payload.pop("guild_id")
        self.author_id = payload.pop("author_id")

        self.timestamp = payload.pop("created_at")

        self.id = payload.pop("id")
        self.key = payload.pop("key")

    def created_at(self,
                   fancy: Optional[bool] = False) -> str:
        """Formats the timestamp appropriately."""

        RAW = "%Y-%m-%d %H:%M:%S.%f"
        FANCY = "%d/%m/%y at %H:%M"

        if fancy:
            return self.timestamp.strftime(format=FANCY)

        return self.timestamp.strftime(format=RAW)

    @property
    def raw_text(self) -> str:
        """Returns the raw text of the archive, this is what you see in the text files."""

        FORMAT = "{timestamp} ({guild} / {channel} / {author} / {message}) {user}: {content} ({attachment})"

        return [FORMAT.format(timestamp=message.created_at(),
                              guild=self.guild_id,
                              channel=message.channel,
                              author=message.author,
                              message=message.id,
                              user=message.username,
                              content=message.content,
                              attachment=message.attachment) for message in self.messages]


class Message(blueprint):
    def __init__(self,
                 json_object: dict):
        self.json = json_object

        self.channel = json_object.pop("channel")
        self.author = json_object.pop("author")
        self.id = json_object.pop("message")
        self.content = json_object.pop("content", None)
        self.attachment = json_object.pop("attachment", None)

        self.username = json_object.pop("username")

        embed = self.json["embed"]

        if embed:
            if embed.get("timestamp") is not None:
                embed["timestamp"] = datetime.strptime(embed["timestamp"], "%Y-%m-%d %H:%M:%S.%f").strftime(format="%d/%m/%y at %H:%M")

            if intable(string=str(embed.get("color")),
                       base=16):
                embed["color"] = "#{0:06X}".format(embed["color"])

            self.embed_data = AttrDict(embed)

        else:
            self.embed_data = None

    def created_at(self,
                   fancy: Optional[bool] = False) -> str:
        """Formats the timestamp appropriately."""

        RAW = "%Y-%m-%d %H:%M:%S.%f"
        FANCY = "%d/%m/%y at %H:%M"

        if fancy:
            return datetime.strptime(self.json["timestamp"], "%Y-%m-%d %H:%M:%S.%f").strftime(format=FANCY)

        return datetime.strptime(self.json["timestamp"], "%Y-%m-%d %H:%M:%S.%f").strftime(format=RAW)

    @property
    def name(self):
        return self.username[:-5]

    @property
    def embed(self):
        return self.embed_data