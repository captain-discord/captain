`gatekeeper` is a system that requires certain (or all) users to verify their legitimacy with a series of special methods.

!!! example
	```yaml
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
	```

## Min age

This is the number of seconds old an account has to be to avoid failing the age check. The default is 7 days.

## Checks for bypass

This setting determines how many checks a user has to pass before they can be auutomatically verified by Captain. If they don't hit this number of checks, they will be required to verify themselves before gaining entry. 

You can set this option to `null` to require all users to verify themselves. This is recommended for large or high-risk servers.

## Type

This integer represents the kind of verification that users will need to complete to gain access. See the table below for reference.

| Verification method | Key |
| ------------------- | --- |
| Run a command       | 0   |
| Complete a captcha  | 1   |

## Action

This determines what will happen when a user is verified. There's a table below for your convenience.

If your server is large or high-risk, it is safer to add a role because it avoids complications during downtime of the bot.

| Action        | Key |
| ------------- | --- |
| Add a role    | 0   |
| Remove a role | 1   |

## Role

This is the ID of the role that will either be added or removed when a user verifies themselves.

## Extras

This should be a dictionary of extra data that is used by a specific type of verification method. At the moment, this only applies to captcha verification (1). See the tables below for help.

### Captcha Verification

| Key           | Explanation                                          |
| ------------- | ---------------------------------------------------- |
| `char_length` | The number of characters in a captcha.               |
| `noise`       | How much image "noise" there should be in a captcha. |
| `attempts`    | How many attempts a user is given per captcha.       |

## What checks are ran?

Currently, there are 2 checks ran on each new user.

### Avatar check

Raiders and automated bot accounts tend to have no avatar. As such, Captain checks whether or not a user has an avatar when it joins and uses that in it's summary of a user's threat level.

### Age check

Almost always, malicious accounts are new and created en masse. As such, a user must be x seconds old to pass this check (though almost all legitimate accounts will pass).