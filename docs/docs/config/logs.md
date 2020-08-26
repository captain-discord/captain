The `logs` option allows you to tell Captain which events should be logged to which channels.

!!! example
	```yaml
	logs:
        123456789098765432: # text channel ID
            - MEMBER_BAN
            - MEMBER_TEMPBAN
            - MEMBER_BAN_EXPIRE
            - MEMBER_UNBAN
            
            - MEMBER_KICK 
            
            - MEMBER_MUTE
            - MEMBER_REMUTE
            - MEMBER_TEMPMUTE
            - MEMBER_MUTE_EXPIRE
            - MEMBER_UNMUTE
            
            - MEMBER_WARN

            - LOCKDOWN
            - LOCKDOWN_TEMP
            - LOCKDOWN_EXPIRE
            - LOCKDOWN_CANCEL
        123456789098765432: # text channel ID
            - MEMBER_JOIN
            - MEMBER_LEAVE
        123456789098765432: # text channel ID
            - MESSAGE_EDIT
            - MESSAGE_DELETE
            - MESSAGE_BULK_DELETE
	```

| Event                 | Key                 |
| --------------------- | ------------------- |
| Member banned         | MEMBER_BAN          |
| Member temp-banned    | MEMBER_TEMP_BAN     |
| Member unbanned       | MEMBER_UNBAN        | 
| Member ban expired    | MEMBER_BAN_EXPIRE   |
| Member kicked         | MEMBER_KICK         | 
| Member muted          | MEMBER_MUTE         |
| Member temp-muted     | MEMBER_TEMP_MUTE    |
| Member re-muted       | MEMBER_REMUTE       |
| Member unmuted        | MEMBER_UNMUTE       |
| Member mute expired   | MEMBER_MUTE_EXPIRE  |
| Member warned         | MEMBER_WARN         |
| Lockdown started      | LOCKDOWN            |
| Temp lockdown started | LOCKDOWN_TEMP       |
| Lockdown expired      | LOCKDOWN_EXPIRE     |
| Lockdown cancelled    | LOCKDOWN_CANCEL     |  
| Member joined         | MEMBER_JOIN         |
| Member left           | MEMBER_LEAVE        |
| Message edited        | MESSAGE_EDIT        |
| Message deleted       | MESSAGE_DELETE      |
| Many messages deleted | MESSAGE_BULK_DELETE |
| Channel created       | CHANNEL_CREATE      |
| Channel deleted       | CHANNEL_DELETE      |
| Role created          | ROLE_CREATE         |
| Role deleted          | ROLE_DELETE         |
| Nickname added        | NICKNAME_ADD        |
| Nickname changed      | NICKNAME_CHANGE     |
| Nickname removed      | NICKNAME_REMOVE     |