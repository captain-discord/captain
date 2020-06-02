# Copyright (C) JackTEK 2018-2020
# -------------------------------

# =====================
# Import PATH libraries
# =====================
# ------------
# Type imports
# ------------
from discord import Guild
from typing import Any, Callable, Iterable, List, Optional, Union


# --------------------
# Builtin dependencies
# --------------------
from datetime import datetime
from json import loads
from random import randint


def dedent(text: str) -> str:
    """Removes any leading whitespace from each line in a string.
    
    This splits the string into lines through \n so this works for single and multi line strings."""

    return "\n".join(line.lstrip() for line in text.split("\n"))

def all(iterable: Iterable[Any],
        condition: Callable) -> List[Any]:
    """Returns all elements that match a given condition in an iterable.
    
    Returns an empty list of no elements matched the condition."""

    return [item for item in iterable if condition(item)]

def first(iterable: Iterable[Any],
          condition: Callable) -> Any:
    """Returns the first item in an iterable that matches a given lambda condition.
    
    Returns None if no item matches the condition."""

    try:
        return next(item for item in iterable if condition(item))

    except StopIteration:
        return None

def intable(obj: Any,
            base: Optional[int] = None) -> Union[int, bool]:
    """Determines whether or not an object can be returned as an integer.
    
    If it can, then the integer is returned, otherwise False is returned."""

    if base is None:
        try:
            return int(obj)
        
        except ValueError:
            return False

    try:
        return int(obj,
                   base=base)

    except ValueError:
        return False

def easter_egg(percentage: int) -> bool:
    """Returns a boolean dictating if an easter egg with a given percentage should be shown."""

    return randint(0, 100) <= percentage


def num_adverb(number: int) -> str:
    """Returns the adverb form of a number.
    
    An example of this is once, twice, 3 times etc."""

    if number == 1:
        return "once"

    elif number == 2:
        return "twice"

    return f"{number} times"

def human_list(values: Any) -> str:
    """Returns a grammatically correct list.
    
    Usually, lists simply use commas to separate every item, however, English grammar states that the last item should have and instead of a comma."""

    if len(values) == 1:
        return values[0]

    return ", ".join(values[:-1]) + f" and {values[-1]}"

def time_since(seconds: int = None,
               since: datetime = None,
               pretty: Optional[bool] = False,
               granularity: Optional[int] = 2,
               skip_empty: Optional[bool] = False,
               ms: Optional[bool] = True) -> Union[dict, str]:
    """Calculates the time in each unit of time.
    
    If seconds is passed, then the values we are finding are of the duration of those seconds.
    If since is passed, then we're finding the values of the seconds between now and the provided datetime.
    If both are provided, since takes priority.

    This normally returns a dictionary in the form::
        {
            "unit": number
        }
        
    However, if the pretty kwarg is provided as True, it will be turned into a more human-readable string that looks something like::
        1 year, 1 month, 1 week, 1 day, 1 hour, 1 minute and 1 second
        
    Granularity refers to the accuracy of the result. This function is accurate from the year to the millisecond.
    Therefore a granularity of 8 will return a result accurate to a millisecond, a granularity of 1 will return a result accurate to the year.
    
    If you don't wish to see values such as 0 years etc. in your result, skip_empty should be parsed as True rather than False.
    This also has an impact on accuracy, if the empties are skipped, the granularity range is decreased.
    
    If you don't want milliseconds to be included in the result, pass ms as False.

    [Note]: If the granularity is higher than the granularity range, the issue is silently ignored and the entire result is returned."""

    result = []
    seconds = (datetime.utcnow() - since).total_seconds() if since else seconds

    for name, count in (("years", 60 ** 2 * 24 * 365), 
                        ("months", 60 ** 2 * 24 * 30), 
                        ("weeks", 60 ** 2 * 24 * 7), 
                        ("days", 60 ** 2 * 24), 
                        ("hours", 60 ** 2), 
                        ("minutes", 60), 
                        ("seconds", 1),
                        ("milliseconds", 1 / 1000)):
        if name == "milliseconds" and not ms:
            continue

        value = seconds // count

        if skip_empty and value == 0:
            continue

        seconds -= value * count

        if value == 1 and pretty:
            name = name.rstrip("s")
        
        result.append((round(number=value), name))

    if pretty:
        return human_list(values=[f"{value} {name}" for value, name in result[:granularity]])

    return {name: value for value, name in result[:granularity]}

def ordinal_indicator(num: int) -> str:
    """Appends the ordinal indicator (th/st etc.) to the end of a number."""

    return "%d%s" % (num,"tsnrhtdd"[(num // 10 % 10 != 1) * (num % 10 < 4) * num % 10::4])

def format_url(**options: dict):
    """Takes in a dictionary of URL options and returns the full connection URL as well as a shortened one.""" 
    
    username = options.pop("username")
    password = options.pop("password")
    auth = ""

    host = options.pop("host")
    port = options.pop("port", None)

    protocol = options.pop("protocol", "http")
    extra = options.pop("extra", "")

    if username:
        auth += username

        if password:
            auth += f":{password}@"

    if options.pop("secure", False):
        protocol += "s"

    return (f"{protocol}://{auth}{host + ':' + str(port) if port is not None else host}{extra}",
            f"{username + '@' if username is not None else ''}{host + ':' + str(port) if port is not None else host}{extra}")

def friendly_user(guild: Guild,
                  id: int) -> str:
    """Returns a friendly representation of a user.
    
    If the user is not found in the guild, then the mention is returned."""

    member = guild.get_member(user_id=id)

    if member is None:
        return f"<@{id}>"

    return str(member)

def string_list(string: str) -> list:
    """Converts a stringified list into a list object."""

    return loads('{"_dump": ' + string + '}')["_dump"]