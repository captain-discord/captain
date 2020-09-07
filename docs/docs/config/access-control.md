In short, the `access_control` section allows server admins to configure which roles are allowed to use what commands.

!!! example
	```yaml
	access_control:
		123456789098765432: # role ID
			level: 100 # 100 = admin (all commands)
		123456789098765432: # role ID
			level: 90 # 90 = mod (all commands except lockdown)
		123456789098765432: # role ID
			level: 90 # the same level can exist more than once
			overwrites: # by denying access to certain commands, this effectively becomes a "trial mod" role
				unban: false # each overwrite is in the format [command name: true/false]
				ban: false
		123456789098765432: # role ID
			level: 10 # 10 = trusted (all non-mod commands + some easter eggs)
		everyone: # everyone = every single member. This could also be a role ID for members, if you want
			level: 0 # 0 = default (non-mod commands)
	```

## Levels and what they mean

A level is sort of like a preset of commands that a role should use. For example, users with the mod level should be able to use Moderation commands, but not Administration commands (such as lockdown and infraction clearing). Below, you'll find a table showing which level ID matches a particular role.

| Role          | Level        |
| ------------- | ------------ | 
| Administrator | 100          |
| Moderator     | 90           | 
| Trusted       | 10           | 
| Default       | 0            |

## Creating your own levels

Currently, there's no way to create your own level designation (e.g. 80 for trial mod), but it is planned. However, you can achieve the same effect by using an existing level as a base then adding overwrites. 

For example, here's what a trial mod level would look like (trial mods may have different access to commands for your server but the idea is the same).

```yaml
access_control:
	123456789098765432: # role ID
		level: 90 # we'll use moderator as a base here
		overwrites:
			ban: false
			unban: false
			inf search: false
			inf recent: false
```

### Breaking it down 

Alright so this look a little scary at first, but I promise it isn't!

To summarise, the example above essentially means: `trial mods can use all mod commands apart from ban, unban, inf search and inf recent`. 

If you're still struggling, the good guys and gals in the [official Discord server](https://discord.gg/EBFhZYY) can give you a hand!

## Hierarchy

The hierarchy for overlapping levels can be incredibly confusing, but I'll try to summarise it anyway.

In short, the user's access to commands is first affected by their highest level. If their highest level doesn't affect a certain command, it will be affected by their second highest level (and this repeats).

If the user has the same level twice that both overwrite the command (assuming the overwrites are different), then the order of the levels in the configuration file determines which takes priority.

!!! summary
	TLDR; if you have a complex system of overlapping levels, it is best to just remove any unnecessary roles from the user that could cause conflicts.