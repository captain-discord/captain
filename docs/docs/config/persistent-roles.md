Configuring persistent roles allows you to tell Captain to add specific roles back to users when they leave and rejoin the server (assuming they had the role when they left).

Often times, you'll want to configure the `infractions.mute_role` to be re-added to muted users when they rejoin the server. This prevents mute-evasion and is crucial to a secure server.

!!! example
	```yaml
	persistent_roles:
        enabled: true
        whitelist:
            - 123456789098765432 # role ID
	```

## Whitelist

This is yet another example of a self-explanatory option but I'll document it anyway. This should be a list of roles that can be re-added by persistent roles (this does NOT include your server's mute role by default, you must add it to this list yourself).