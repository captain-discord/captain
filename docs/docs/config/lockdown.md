You can control a handful of options for locking down channels with the `lockdown` option.

!!! example
	```yaml
	lockdown:
        locked_role: everyone # or role ID
        whitelist:
            - 123456789098765432 # role ID
	```

## Locked role

This option allows you to change which role is given the channel override that stops them from speaking. Most of the time, this should be `everyone`, but it could also be the ID of a role that most/all members have.

## Whitelist

This is a list of roles that are specifically allowed to talk during a lockdown. Often times, this will be for Moderators and trusted people.