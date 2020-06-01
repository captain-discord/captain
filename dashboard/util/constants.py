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


config = AttrDict(safe_load(stream=open(file="config.yml")))
const = AttrDict(dict(version=version(**config.version)))

app = None
postgres = None