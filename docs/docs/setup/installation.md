## Cloning the Repository

First thing's first, clone the repository!
```
git clone https://github.com/Jack-Gledhill/captain
```

## Configuration files

In both the `bot/` and `web/` directories, there'll be 2 files. They're `config.example.yml` and `core/constants.example.py`! You'll need to edit them and remove the `.example` from their name.

## Deploying a Captain container

Since we have multiple services, we can use a tool called Docker Compose to greatly simplify the deployment process.

To run Captain and all other subsidiaries, cd into `captain` then run the following command.
```
docker-compose up -d
```

## Additional support

:tada: Congratulations, you have officially set up your own Captain bot! If, somehow, you haven't, then join the [official Discord server](https://discord.gg/EBFhZYY) and we'll be happy to lend a hand!