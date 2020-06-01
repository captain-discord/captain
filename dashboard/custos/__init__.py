# Copyright (C) Mila Software Group 2018-2020
# -------------------------------------------
# This is the main file, this is the file that is imported.

# Introduction to commenting
# --------------------------
# All comments within these files will be surrounded by lines to make them stand out.

# = will mark a heading of a particular process
# - will mark a sub-heading of a particular process
# ~ will mark an explanation of the code directly below

# =====================
# Import PATH libraries
# =====================
# -----------------
# Builtin libraries
# -----------------
import os

from datetime import datetime

# ---------------
# Local libraries
# ---------------
from custos.logger import *
from custos.blueprints import *

# ==============================
# Check for missing dependencies
# ==============================
try:
    import termcolor

except ImportError as error:
    now = datetime.utcnow()
    
    print(f"{now.strftime('%d-%m-%Y')} {now.strftime(format='%H:%M:%S')}:{str(round(number=int(now.strftime(format='%f'))/1000)).rjust(3, '0')} \x1b[31mFATAL\x1b[0m  [\x1b[32mcustos:\x1b[0m\x1b[34minit\x1b[0m]: {error.name} dependency is missing.")
    
    os._exit(status=2)

# ============================================
# This is for semantic versioning (aka semver)
# ============================================
version_info = version(major=1,
                       minor=0,
                       patch=0,
                       release="stable")