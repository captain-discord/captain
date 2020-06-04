# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# -------------------------
# Local extension libraries
# -------------------------
from custos import blueprint


class InfractionType(blueprint):
    UNKNOWN  = -1
    WARN     = 0
    MUTE     = 1
    TEMPMUTE = 2
    SOFTBAN  = 3
    BAN      = 4
    TEMPBAN  = 5
    KICK     = 6