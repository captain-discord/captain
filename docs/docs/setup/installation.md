## Cloning the Repository

First thing's first, clone the repository!
```
git clone https://github.com/Jack-Gledhill/captain
```

## Configuration files

1. Make sure to cd into the captain/bot directory.
2. Now you need to edit 2 files. These two files are `config.example.yml` and `guilds.example.yml`, you need to rename them to have the `.yml` without the `.example` then edit them.
3. Lastly, you'll need to rename `core/constants.example.py` to `core/constants.py` then edit it. This file contains information for the core, like the bot's token and presence information.

## Deploying a Captain container

Deploying a container needs to be done in two steps. First you need to build the image, 	then you need to run an instance of that image. It's easy though so don't worry!

To build an image, cd into `captain/bot` then run `docker build`.
```
docker build . --tag captain:3.1.0
```

Now all that's left to do is run an instance of the container with `docker run`.
```
docker run -d --name captain --network="host" captain:3.1.0
```

## Additional support

:tada: Congratulations, you have officially set up your own Captain bot! If, somehow, you haven't, then join the [official Discord server](https://discord.gg/pWraGYX) and we'll be happy to lend a hand!