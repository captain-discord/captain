The `custom_commands` option allows guild owners to specify a list of commands with their own names. You can use this to send a message, or toggle a role on a user. The second option is useful because it essentially acts like an alternative to reaction roles (we call this self-assign roles). 

!!! example
	```yaml
	custom_commands:
        - name: lorem
          action: 0
          value: "{ctx.author.mention} Lorem ipsum dolor sit amet"
        - name: ipsum
          action: 1
          value: 123456789098765432 # role ID
	```

## Name

This is the actual name of the command that you want to create. To actually call the command, you'd send a message with the bot's prefix followed directly by the command name. 

For example, if the prefix is `!` and the name is `hello`, the command would be `!hello`.

!!! note
	Due to some limitations, custom commands does not yet support mentioning the bot as a prefix.

## Action

This allows you to specify what will happen when someone uses the custom command. Refer to the table below for details.

| Action       | Key |
| ------------ | --- |
| Send message | 0   |
| Toggle role  | 1   |

## Value

Depending on the action chosen, this will either be some text (for the send message action) or a role ID (for the toggle role action).

!!! note
	The value of a custom command with the send message action has formatting access to context via `ctx`. E.g. to mention the user that used the command, just add `{ctx.author.mention}` to the value! See the [discord.py documentation](https://discordpy.readthedocs.io/en/latest/ext/commands/api.html#context) for details.