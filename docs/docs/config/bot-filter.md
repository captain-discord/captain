The `bot_filter` options allow you to filter out certain bots that could be potentially dangerous. This is only recommended for servers that require top-notch control and can't take any risks with an opening for a raid in some way.

!!! example
	```yaml
	bot_filter:
		enabled: true
		require_verification: true
		min_age: 86400

		whitelist:
			- 123456789098765432 # bot ID
	```

## Require verification

If set to true, bots joining the server must have the Verified checkmark given to bots by Discord. In other words, a bot that is in more than 100 guilds and has been manually reviewed by Discord.

## Min age

The number of seconds old a bot must be for it to pass the age check.

## Whitelist

This should be a list of IDs pertaining to bot accounts that you want to whitelist from the filter.