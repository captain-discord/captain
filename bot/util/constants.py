# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# -------------------------
# Local extension libraries
# -------------------------
from custos import version

# ------------------------
# Third-party dependencies
# ------------------------
from attrdict import AttrDict
from yaml import safe_load


actions = AttrDict(safe_load(stream=open(file="actions.yml")))
cache = AttrDict(dict(first_ready_time=None,
                      plugins=[],
                      presence=None,
                      avatar_url=None))

config = AttrDict(safe_load(stream=open(file="config.yml")))
const = AttrDict(dict(version=version(**config.version)))

emojis = None
guilds = AttrDict(safe_load(stream=open(file="guilds.yml")))
postgres = None
redis = None