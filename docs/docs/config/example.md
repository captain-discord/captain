```yaml
# Action ID guide
# ---------------
# 1 = ban
# 2 = mute
# 3 = warn
# 4 = do nothing

# Custom Command Action ID Guide
# ------------------------------
# 0 = send message
# 1 = toggle role

# Roles for Badges Flags
# ----------------------
# 1      = Discord Staff
# 2      = Discord Partner
# 4      = HypeSquad Events Member
# 8      = Bug Hunter
# 64     = HypeSquad Bravery
# 128    = HypeSquad Brilliance
# 256    = HypeSquad Balance
# 512    = Early Supporter
# 16384  = Gold Bug Hunter
# 131072 = Verified Bot Developer

# Verification Types
# ------------------
# 0 = agree command
# 1 = captcha verification

# Verification Actions
# --------------------
# 0 = add role
# 1 = remove role

# Web Access
# ----------
# 0 = view and edit
# 1 = view only

nickname: Captain Hook # any text you want (max 32 chars)

web:
    123456789098765432: 0 # user ID
    123456789098765432: 1 # user ID

gatekeeper:
    enabled: true
    
    min_age: 604800
    checks_for_bypass: 2 # null will disable auto-bypassing

    type: 1
    action: 1
    role: 123456789098765432 # role ID
    
    extras:
        char_length: 6
        noise: 0.6
        attempts: 3

bot_filter:
    enabled: true
    require_verification: true
    min_age: 86400

    whitelist:
        - 123456789098765432 # bot ID

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

access_control:
    123456789098765432: # role ID
        level: 100
        overwrites:
            ping: false # command name: true or false
    everyone: # or role ID
        level: 0

infractions:
    mute_role: 123456789098765432 # role ID
    ban_purge_days: 7

auto_roles: 
    123456789098765432: # role ID
        - HUMAN
    123456789098765432: # role ID
        - BOT

reaction_roles:
    enabled: true
    channel: 123456789098765432 # text channel ID
    message: 123456789098765432 # message ID
    roles:
        123456789098765432: ✅ # role ID: unicode emoji or custom emoji (<:name:id>)

starboard:
    enabled: true
    emoji: ⭐ # unicode emoji or custom emoji (<:name:id>)
    required_stars: 1
    channel: 123456789098765432 # text channel ID

    ignored_roles:
        - 123456789098765432 # role ID
    ignored_channels:
        - 123456789098765432 # text channel ID

lockdown:
    locked_role: everyone # or role ID
    whitelist:
        - 123456789098765432 # role ID

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
        
anti_link:
    enabled: true
    action: 2
    duration: 3600

    ignored_roles:
        - 123456789098765432 # role ID
    ignored_channels: 
        - 123456789098765432 # text channel ID
    whitelist: 
        - https://captainbot.xyz

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
        
stat_counters:
    123456789098765432: # voice channel ID
        event: MEMBER_COUNT_CHANGE # BOT_COUNT_CHANGE, HUMAN_COUNT_CHANGE, NEWEST_BOT, NEWEST_HUMAN or NEWEST_MEMBER
        format: "{value}"
        
persistent_roles:
    enabled: true
    whitelist:
        - 123456789098765432 # role ID

custom_commands:
    - name: lorem
        action: 0
        value: "{ctx.author.mention} Lorem ipsum dolor sit amet"
    - name: ipsum
        action: 1
        value: 123456789098765432 # role ID
```