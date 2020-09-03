import core.prefix as prefix

from datetime import datetime
from random import choice
from re import finditer
from string import ascii_lowercase, ascii_uppercase, digits


def dedent(text):
	"""Removes any leading whitespace from each line in a string.
	
	This splits the string into lines through \n so this works for single and multi line strings."""

	return "\n".join(line.lstrip() for line in text.split("\n"))

def first(iterable, condition):
	"""Returns the first item in an iterable that matches a given lambda condition.
	
	Returns None if no item matches the condition."""

	try:
		return next(item for item in iterable if condition(item))

	except StopIteration:
		return None

def human_list(values):
	"""Returns a grammatically correct list.
	
	Usually, lists simply use commas to separate every item, however, English grammar states that the last item should have and instead of a comma."""

	if len(values) == 1:
		return values[0]

	return ", ".join(values[:-1]) + f" and {values[-1]}"

def time_since(seconds=None, since=None, pretty=True, granularity=8, skip_empty=True, ms=False):
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
		
		result.append((round(value), name))

	if pretty:
		return human_list([f"{value} {name}" for value, name in result[:granularity]])

	return {name: value for value, name in result[:granularity]}

def ordinal_indicator(num):
	"""Appends the ordinal indicator (th/st etc.) to the end of a number."""

	return "%d%s" % (num,"tsnrhtdd"[(num // 10 % 10 != 1) * (num % 10 < 4) * num % 10::4])

def shorten(text, length, add="..."):
	"""Shortens the provided text if it's longer than the length.
	
	If it's longer, add is appended to the end."""

	if text is None:
		return ""

	shortened = text[:length - len(add)]

	if shortened != text:
		return shortened + add

	return shortened

def gen_jump_url(message_id, channel_id, guild_id=None):
	"""Generates a jump URL for a particular message in a particular channel in an optional guild."""

	BASE = "https://discord.com/channels/"

	if guild_id:
		return BASE + f"{guild_id}/{channel_id}/{message_id}"

	else:
		return BASE + f"{channel_id}/{message_id}"

def spacer(text, times, char="\u2000"):
	"""Prepends a specified number of the char value to the text.
	
	Handy for neatly appending special space characters two or three times."""

	return char * times + text

def identifier(fmt):
	"""Generates a new identifier with a given format.
	
	The format uses percent codes, the following codes are available::
		%d A single 0-9 digit
		%a A single upper/lower a-Z letter
		%l A single a-z lowercase letter
		%L A single A-Z uppercase letter
		%s A single symbol (e.g. @ or #)"""

	SYMBOLS = r"!\"£$%^&*()-=[]{};'#:@~,./<>?`¬|"

	digit_codes = [code.start() for code in finditer("%d", fmt)]
	letter_codes = [code.start() for code in finditer("%a", fmt)]
	letter_digit_codes = [code.start() for code in finditer("%A", fmt)]
	lower_codes = [code.start() for code in finditer("%l", fmt)]
	upper_codes = [code.start() for code in finditer("%L", fmt)]
	symbol_codes = [code.start() for code in finditer("%s", fmt)]
	random_codes = [code.start() for code in finditer("%r", fmt)]

	result = list(fmt)
	for code in digit_codes:
		result[code] = choice(digits)
		result[code+1] = ""

	for code in letter_codes:
		result[code] = choice(ascii_lowercase + ascii_uppercase)
		result[code+1] = ""

	for code in letter_digit_codes:
		result[code] = choice(digits + ascii_lowercase + ascii_uppercase)
		result[code+1] = ""

	for code in lower_codes:
		result[code] = choice(ascii_lowercase)
		result[code+1] = ""

	for code in upper_codes:
		result[code] = choice(ascii_uppercase)
		result[code+1] = ""

	for code in symbol_codes:
		result[code] = choice(SYMBOLS)
		result[code+1] = ""

	for code in random_codes:
		result[code] = choice(SYMBOLS + ascii_lowercase + ascii_uppercase + digits)
		result[code+1] = ""

	return "".join(result)

def bytes_4_humans(count):
    if 1024 > count >= 1:
        return f"{round(count, 2)} B"

    if 1024 > count / 1024 >= 1:
        return f"{round(count / 1024, 2)} KB"

    if 1024 > count / 1024 ** 2 >= 1:
        return f"{round(count / 1024 ** 2, 2)} MB"

    if 1024 > count / 1024 ** 3 >= 1:
        return f"{round(count / 1024 ** 3, 2)} GB"

    if 1024 > count / 1024 ** 4 >= 1:
        return f"{round(count / 1024 ** 4, 2)} TB"

    return f"{round(count / 1024 ** 5, 2)} PB"

def clean_user(guild, user_id):
	member = guild.get_member(user_id)

	if member is not None:
		return member

	return user_id

def fmt_prefix(command):
	return prefix.default + command