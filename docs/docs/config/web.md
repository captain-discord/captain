The `web` option allows you to configure a set of user IDs that can either view or edit the guild's settings via the web dashboard. See the table below for help on access keys

!!! example
	```yaml
	web:
		123456789098765432: 0 # user ID
		123456789098765432: 1 # user ID
	```

| Access      | Key |
| ----------- | --- |
| View & edit | 0   |
| View only   | 1   |

!!! note
	The server owner and anyone with the Manage Server or Administrator permissions are able to edit the guild's settings **regardless of whether or not they're configured here**.