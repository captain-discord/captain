Statistics counters are special see-only voice channels that are used to provide an overview of a server's statistics.

For example, you could have a voice channel that shows how many members are currently in the server. Or, you could have one that shows the name of the newest member.

!!! example
	```yaml
	stat_counters:
        123456789098765432: # voice channel ID
            event: MEMBER_COUNT_CHANGE # BOT_COUNT_CHANGE, HUMAN_COUNT_CHANGE, NEWEST_BOT, NEWEST_HUMAN or NEWEST_MEMBER
            format: "{value}"
	```

## Event

This option specifies what statistic the provided channel will show. Refer to the table below for information on which events are currently available.

| Event                                 | Key                 |
| ------------------------------------- | ------------------- |
| Someone joined/left the server        | MEMBER_COUNT_CHANGE |
| A bot account joined/left the server  | BOT_COUNT_CHANGE    |
| A regular user joined/left the server | HUMAN_COUNT_CHANGE  |
| The newest user/bot                   | NEWEST_MEMBER       |
| The newest bot account                | NEWEST_BOT          |
| The newest regular user               | NEWEST_HUMAN        |

## Format

This is a format string used to determine the new name of the voice channel once the event triggers. You only have one formatting option available to you and that is `value` (so you would type `{value}` to indicate where that value belongs).

For example, if I wanted to show the total number of server members, the format would be something like `Members: {value}`.