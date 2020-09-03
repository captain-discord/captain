import discord, re

from discord.ext import commands

class BanCandidateConverter(commands.Converter):
	async def convert(self, ctx, argument):
		try:
			return await commands.MemberConverter().convert(ctx, argument)

		except commands.BadArgument:
			try:
				return await commands.UserConverter().convert(ctx, argument)

			except commands.BadArgument:
				try:
					user_id = int(argument)

				except ValueError:
					raise commands.BadArgument()

				try:
					return await ctx.bot.fetch_user(user_id)

				except discord.NotFound:
					raise commands.BadArgument()


class DurationConverter(commands.Converter):
	TIME_DICT = {
		"s": 1, 
		"sec": 1,
		"secs": 1,
		"second": 1,
		"seconds": 1,
		
		"m": 60, 
		"min": 60,
		"mins": 60,
		"minute": 60,
		"minutes": 60,	
		
		"h": 3600, 
		"hr": 3600, 
		"hrs": 3600, 
		"hour": 3600,
		"hours": 3600,
		
		"d": 86400,
		"day": 86400,
		"days": 86400,

		"w": 604800,
		"wk": 604800,
		"wks": 604800,
		"week": 604800,
		"weeks": 604800,

		"mth": 86400 * 30,
		"mths": 86400 * 30,
		"month": 86400 * 30,
		"months": 86400 * 30,

		"y": 86400 * 365,
		"yr": 86400 * 365,
		"yrs": 86400 * 365,
		"year": 86400 * 365,
		"years": 86400 * 365
	}
	TIME_REGEX = re.compile(rf"(?:([0-9]+)\s?({'|'.join(key for key in TIME_DICT.keys())}))+?")

	async def convert(self, ctx, argument):
		time = 0
		
		for v, k in re.findall(self.TIME_REGEX, argument.lower()):
			try:
				time += self.TIME_DICT[k] * float(v)
		
			except (KeyError, ValueError):
				raise commands.BadArgument()

		if time == 0:
			raise commands.BadArgument()
		
		return time