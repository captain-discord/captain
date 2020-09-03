Whenever a new Captain update arrives, you'll probably want to get it. This guide runs through the simple process of updating your Captain instance!

## Pull the repository

The first step is to download the new repository code.
```
git pull
```

!!! warning
	You may find that new sections have been added to the configuration files. If so, you'll need to update your existing configuration files appropriately!

## Recreating the image

Next, you'll need to recreate the Docker image for Captain. This is a pretty simple task, much like the one in the [installation](/setup/installation) guide.

1. First of all, make sure to cd into the `captain/bot` directory.
2. Now run `docker build` like so:
```
docker build . --tag captain:3.2.0
```

## Redeploying the container

Redeploying Captain is a little more long-winded but should be an easy task. 

The first task is to stop the running container.
```
docker stop captain
```

After that, you'll need to remove the container.
```
docker rm captain
```

Now, you're ready to recreate the container just like you did before!
```
docker run -d -v ~/captain/bot/guilds.yml:/opt/bot/guilds.yml -v ~/captain/bot/config.yml:/opt/bot/config.yml -v ~/captain/bot/core/constants.py:/opt/bot/core/constants.py --name captain --network="host" captain:3.2.0
```

!!! note
	If your clone's directory is located somewhere other than `~/captain`, you will need to change the bind-mounts for the config files.