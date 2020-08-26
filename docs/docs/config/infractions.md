The `infractions` config options allow you to specify a handful of settings that change how infractions are carried out by the bot.

!!! example
	```yaml
	infractions:
		mute_role: 123456789098765432 # role ID
		ban_purge_days: 7 # any number between 0 and 7
	```

## Mute role

In short, the `mute_role` is the ID of the role that is added/removed from users when they are muted/unmuted respectively. 

## Ban Purge Days

The `ban_purge_days` is the number of days worth of recent messages that will be deleted when a user is banned. This is actually a part of Discord so there isn't much room to expand upon this.