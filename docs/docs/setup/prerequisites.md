## A host

The first, and most important, thing you'll need is a host. This can be a dedicated server (this could be an enterprise-grade server or just an old computer) or a virtual server (AKA VPS). Either way, the important thing you'll need is 24/7 uptime (or close to it).

There are many providers out there that you can rent VPSs or dedicated servers from. Personally, I rent a 4 core, 8 GB RAM VPS from [Contabo](https://contabo.com) at £4.50/m (about $5.90/m or 5 euros/m).

**Important note:** the host you use _MUST_ be running a Linux distribution! This guide assumes you're using a Ubuntu host, but any Linux host will have similar setup instructions.

## Git

Git is an important CLI tool that's usually already installed on most Linux distributions. If it isn't, run the command below.
```
sudo apt-get install git
```

## PostgreSQL

You'll also need a [PostgreSQL](https://postgres.org) server. In layman's terms, this is a database. I recommend using [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-postgresql-on-ubuntu-18-04) if you're using an Ubuntu server. If you're not using Ubuntu, I'm sure a quick Google search for your specific distro should do it.

## Docker

[Docker](https://docker.com) is a piece of software we use to place other software into what we call a "container". In simple terms, a container is an isolated environment that gives users superior control over the software they're running. 

I use [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04) to get Docker up and running properly.

## Docker Compose

Docker Compose allows us to easily and quickly deploy several services at once with a single, easy to remember command. 

See [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-compose-on-ubuntu-20-04) for setup instructions.

## Redis

The final prerequisite is Redis. Redis is an in-memory database (in other words a cache) that Captain uses to temporarily store information for spam detection. You'll find that [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04) will prove useful.

As long as you run your Redis server on the same host as Captain, there isn't much need to setup a password since the information only lasts for a few seconds and doesn't reveal anything secret. Besides, only software on your host could access Redis in the first place.