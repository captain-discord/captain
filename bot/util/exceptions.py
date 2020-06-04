# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from discord import User
from typing import Any


# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint


class ArtemisException(blueprint, Exception):
    pass


class UserNotFound(ArtemisException):
    def __init__(self,
                 query: Any):
        self.query = query