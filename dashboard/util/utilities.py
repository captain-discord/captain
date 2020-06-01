# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from typing import Callable, List, Optional, Union


# --------------------
# Builtin dependencies
# --------------------
from random import choice
from string import ascii_letters, digits

# ------------------------
# Third-party dependencies
# ------------------------
from flask import jsonify


def intable(string: str,
            base: Optional[int] = 10) -> Union[int, bool]:
    """Queries whether a string can be turned into an integer.
    
    If it can, the integer value is returned."""

    if isinstance(string, int):
        return string

    try:
        return int(string, base=base)

    except ValueError:
        return False
    
    except TypeError:
        return False

def gen_id() -> str:
    """This generates an ID for an archive.
    
    Since the Postgres table sees the ID as a varchar to increase performance, the format has to be hard coded."""

    FORMAT = "{0}-{1}-{2}-{3}"
    
    CHARS_PER_SECTION = 4
    SECTIONS = 4

    return FORMAT.format(*["".join(choice(ascii_letters + digits) for i in range(CHARS_PER_SECTION)) for i in range(SECTIONS)])


def respond(code: Optional[int] = 200,
            msg: Optional[str] = "OK",
            **extras: dict):
    """Responds with a JSON payload."""

    return jsonify(dict(code=code,
                        message=msg,
                        **extras)), code