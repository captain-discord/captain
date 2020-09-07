Whenever a new Captain update arrives, you'll probably want to get it. This guide runs through the simple process of updating your Captain instance!

## Pull the repository

The first step is to download the new repository code.
```
git pull
```

!!! warning
	You may find that new sections have been added to the configuration files. If so, you'll need to update your existing configuration files appropriately!

## One command to do it all

This process is even easier than deploying the bot for the first time, just run `docker-compose up` like you did last time!
```
docker-compose up -d --build
```