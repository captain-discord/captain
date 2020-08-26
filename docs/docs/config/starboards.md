Starboars are a way to allow users to upvote messages by reacting to it, often using a star emoji. Once a message has received enough upvotes (upvotes from bot accounts and the message author are ignored), it will be posted to a special channel.

This essentially allows the community to save funny, memey or otherwise important messages so that they can easily be found again.

!!! example
	```yaml
	starboard:
        enabled: true
        emoji: ⭐ # unicode emoji or custom emoji (<:name:id>)
        required_stars: 1
        channel: 123456789098765432 # text channel ID

        ignored_roles:
            - 123456789098765432 # role ID
        ignored_channels:
            - 123456789098765432 # text channel ID
	```

## Emoji

This is the emoji that users will need to react with in order to upvote a message. It could be a unicode emoji, or a custom Discord emoji in the format `<:name:id>`.

## Required stars

This is pretty obvious. The number represents how many stars are required for a message to be posted to the starboard channel.

## Channel

This is the ID of the starboard channel where starred messages are sent.

## Ignored roles & Ignored channels

These two are pretty simple. Ignored roles is a list of roles that cannot star messages (if a user has any of these roles, their upvote will be ignored). Similarly, ignored channels is a list of channels where messages cannot be uploaded to the starboard channel.