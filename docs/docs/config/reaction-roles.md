Sometimes, you'll find that you want a way for users to select a handful of vanity (or otherwise utility) roles such as colours and roles that give you access to more specific content like a gamer discussion channel.

Insert reaction roles. In a nutshell, users can select a variety of configured roles by reacting (or unreacting) to a specific message with a specific emoji.

!!! example
	```yaml
	reaction_roles:
        enabled: true
        channel: 123456789098765432 # text channel ID
        message: 123456789098765432 # message ID
        roles:
            123456789098765432: ✅ # role ID: unicode emoji or custom emoji (<:name:id>)
	```

## Channel

Because of a Discord API limitation, you need to provide the channel where the message is located.

## Message

This is the message that users will be reacting to. Usually, this is in an otherwise empty channel that regular members cannot type in.

The message's content will not be provided for you, so you'll have to tell users which emoji will give them which role.

## Roles

This should be a key-value pair where the key is a role ID and the value is either a unicode emoji or a custom Discord emoji (this will be found in the format `<:name:id>`).