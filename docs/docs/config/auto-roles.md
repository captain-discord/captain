By configuring `auto_roles`, you can tell Captain to assign specific roles to new users. You can even decide to give a role to any new bots that join, but not regular users (and vice versa).

!!! example
	```yaml
	auto_roles: 
		123456789098765432: # role ID
			- HUMAN
		123456789098765432: # role ID
			- BOT
	```

| User Type    | Key   |
| ------------ | ---   |
| Regular user | HUMAN |
| Bot account  | BOT   | 