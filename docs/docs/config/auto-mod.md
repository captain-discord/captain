This page compiles 4 different configuration options into 1 since they're all very similar.

## Anti spam

This is simple. If a user sends X messages within Y seconds, do Z action.

!!! example
	```yaml
	anti_spam:
        enabled: true
        action: 2
        duration: 3600

        count: 5
        threshold: 5

        ignored_roles:
            - 123456789098765432 # role ID
        ignored_channels: 
            - 123456789098765432 # text channel ID
	```

## Anti ping-spam

This is similar to anti-spam but it only counts the number of people a user has mentioned recently.

!!! example
	```yaml
	anti_ping_spam:
        enabled: true
        action: 2
        duration: 3600

        count: 10
        threshold: 60

        ignored_roles:
            - 123456789098765432 # role ID
        ignored_channels: 
			- 123456789098765432 # text channel ID
	```

## Anti curse

This blocks a list of words. Often times, these words will be curses and derogatory terms.

!!! example
	```yaml
	anti_curse:
        enabled: true
        action: 2
        duration: 3600

        ignored_roles:
            - 123456789098765432 # role ID
        ignored_channels: 
            - 123456789098765432 # text channel ID
        blacklist: 
            - nigga
			- faggot
	```

## Anti invite

Does what it says on the tin; stops users from sending invite links to other Discord servers.

!!! example
	```yaml
	anti_invite:
        enabled: true
        action: 2
        duration: 3600

        ignored_roles:
            - 123456789098765432 # role ID
        ignored_channels: 
            - 123456789098765432 # text channel ID
        whitelist: 
            - discord-developers
            - discord-testers 
            - discord-events
	```

!!! note
	Invites for the server will be ignored by Captain.

## Action

This is a numerical value ranging from 1-4 that determines which action should be taken when a user triggers auto-mod. Refer to the table below to see which number matches which action.

| Action  | Key |
| ------  | --- |
| Ban     | 1   |
| Mute    | 2   |
| Warn    | 3   |
| Nothing | 4   | 

!!! note
	No matter what the provided action number is, the message(s) that triggered auto-mod will be deleted.

## Duration

If the action is set to 1/2 (ban/mute), the duration tells Captain how long the punishment should last. I.e. if the action is ban and the duration is 3600, any users that trigger auto-mod will be banned for an hour.

## Count

**This option is specific to anti spam and anti ping spam.**

This is the number of occurances that Captain will tolerate before invoking an action on the user. For example, setting this to `5` for anti spam means that a user needs to send 5 messages within the configured time period to trigger anti spam.

## Threshold

**This option is specific to anti spam and anti ping spam.**

This is the time period that a user has to trigger anti spam or anti ping spam. Usually, this should be pretty short for anti spam and pretty long for anti ping spam.

Still don't understand? OK then. If the count and threshold for anti spam are both 5, that means a user has to send 5 messages within 5 seconds to trigger anti spam.

## Ignored roles & Ignored channels

Hopefully self-explanatory. If a user has ANY of the ignored roles, they are exempt from that specific auto-mod feature. If the message was sent in one of the ignored channels, auto-mod ignores it. You get the drift? Good.

## Blacklist

**This option is specific to anti curse.**

This should be a list of words that are blocked by Captain. This will likely be populated by a list of derogatory terms and perhaps curse words (if you choose to block them in your server).

## Whitelist

**This option is specific to anti invite.**

This is a list of Discord invites that Captain will not filter. Usually, invites to official Discord servers, affiliated servers and other verified servers belong here.

You wouldn't want to block the Fortnite official server invite now would you? :smirk: