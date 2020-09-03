`roles_for_badges` is a system I invented to assign roles to users depending on the Discord badges they have. For example, Discord Partners will receive a role called "Discord Partner", or something along those lines.

!!! example
	```yaml
	roles_for_badges:
		enabled: true
		sync_on:
			- JOIN
		flags:
			1: 123456789098765432 # role ID
			2: 123456789098765432 # role ID
			4: 123456789098765432 # role ID
			8: 123456789098765432 # role ID
			64: 123456789098765432 # role ID
			128: 123456789098765432 # role ID
			256: 123456789098765432 # role ID
			512: 123456789098765432 # role ID
			16384: 123456789098765432 # role ID
			131072: 123456789098765432 # role ID
	```

## Sync on

This option specifies a list of events where Captain can automatically synchronise a user's roles. See the table below for reference.

| Event       | Key  |
| ----------- | ---- |
| User joined | JOIN |

!!! note
	Due to a limitation with the Discord API, there's no sane way to update a user's roles when they receive a new badge (or lose one).

## Flags

This is a key-value mapping where the key is the flag integer used by the Discord API to denote a specific badge. E.g. 1 = Discord Staff, see the table below for info. The value should be the role that corresponds with the flag.

| Badge            | Flag   |
| ---------------- | ------ |
| Discord Staff    | 1      |
| Discord Partner  | 2      |
| HS Events        | 4      |
| Bug Hunter       | 8      |
| HS Bravery       | 64     |
| HS Brilliance    | 128    |
| HS Balance       | 256    | 
| Early Supporter  | 512    |
| Bug Hunter Lvl 2 | 16384  |
| Verified Bot Dev | 131072 |