# The Vyos Hacker Toolkit

Hacking VyOS should be fun and easy. This tool make it so (easy, it was already fun).

My day to day machine runs OSX, unfortunately it is not possible to compile the VyOS ISO directly on MacOS (even using Docker - at least until they implement mknod), so I needed a Linux Virtual Machine for it. I also like to have an agreable workflow so I started working on some code to automate my most common tasks, which evolved from a small number of shell script to this python project.

But should you be developing on Linux, setting your build server to 127.0.0.1:22 will cause the program to use the current user on the local machine and will surely make hacking on VyOS easier and more agreable.

So if you need to:
 * build (and test) the VyOS ISO
 * update VyOS to the latest rolling (including using the latest rolling)
 * branch and edit code from your VyOS github repository
 * push codes change to a router

Then read on.

## Quick Installation

The tools can be run directly from the source code folder but it may be easiest to build a zipapp (a self contain python program) from the provided tools and move it in your $PATH.

It can be done as following:
```
git clone git@github.com:thomas-mangin/vyos-extra
cd vyos-extra
./release /usr/local/bin/vyos
cp ./etc/vyos-extra.conf.sample ~/.config/vyos/extra.conf
```

Then edit ` ~/.config/vyos/extra.conf` to configure your build server(s) and router(s).
And finally setup your build server (or local machine)

```
vyos setup build
```

The application can also be installed using `setup.py`, or ran directly from the repository, but until there is a PyPI release, building the zipapp is the recommended way.

You should setup one build server (normally called build) where the tools will setup a VyOS development environment, and one router where you can test new image / code change, it is possible to have more.

While the configuration file is the prefered configuration way, it is also possible to use environment variable (which will take precedence), prepending the name with "VYOS_", and using the same name in upper case.

For example, doing this to change which email get into a VyOS ISO
```
env VYOS_GLOBAL_EMAIL=ci@buiness.com vyos make iso
env VYOS_ROUTER_USER=thomas vyos ssh router
```

## Tools

All the tools are available through the `vyos` entry point, the commands are:

| names     | Description |
| ---       | --- |
| branch    | clone and branch a VyOS repository
| download  | download (if required) and cache the lastest VyOS rolling
| edit      | work on a branch repository
| iso       | build a vyos rolling ISO (and possibly test it)
| make      | call other make function than iso
| package   | build and install a VyOS package (vyos-1x, ...).
| setup     | setup a VyOS machine (build or router) for development.
| ssh       | ssh to a configured server
| test      | perform some test on the VM
| update    | update a VyOS router with vyos-1x.
| upgrade   | download (if required), cache, and serve locally the lastest rolling

the command `make`, `iso` and `update` will require a working build server.

This can be done by using the the `setup` command for Debian/Ubuntu (only OS supported ATM).

using `-s/--show` will present you with what the tool is going to do without running any command.
```
# ./bin/vyos ssh router --show
ssh  -i /Users/thomas/.ssh/id_rsa.personal -p 2200 vyos@127.0.0.1
```

Using the `update` feature require the router to have been prepared with `setup`.

Note:
 * This is a developer tool, we expect its user to be able to self-help and only report bugs
 * Only a few files are copied by `vyos update` make sure all your changes are copied across
 * The syntax of the tools is still changing

## Setup

In the configuration file, create a name for yours hosts and define how to connect to them.
In the case of a build server (used to compile VyOS) using 127.0.0.1 and port 22, will skip using SSH.

For example, here we will use our local machine `build` and and connect to a vyos router called `router`:

```
[build]
role = build
host = 127.0.0.1
port = 22
user = 
file = 
repo = $HOME/vyos/vyos-build
default = True

[router]
role = router
host = 127.0.0.1
port = 2200
user = vyos
file = ~/.ssh/mykey
default = True

[global]
store = /tmp/
email = vyosbuild@vyos.net
github = thomas-mangin
editor = vscode
cloning_dir = ~/.config/vyos/clone
working_dir = ~/vyos/

```

You will also have to use github to fork the vyos project you want to work on.
If you just want to build a package, you can change the `github` user to `vyos`s.

## Local setup

On mac, the following tools shoulld installed with [HomeBrew](https://brew.sh)) for the tool to work.
```
brew install git
brew install rsync
```

## How to use ?

*setting up the build server in the configuration*
```
vyos setup build
```

*working on a phabricator issue*
```
vyos branch T2000
cd ~/vyos/T2000
# ..hack
# ... vi vyos-1x
vyos build
# .... compile vyos-1x and deploy it on your default router
```

*Updating a router to the latest rolling*
```
vyos upgrade router
# .. download the latest rollin (and cache it)
# ... update the router
# .... and reboot it
```

*ssh to one of the router/build machine (by name)*
```
vyos ssh router
# . the same could be done with .ssh/config if you like to duplicate conf files :-)
```

*convert a vyos router into a development one*
```
vyos setup router
```

You can run all the commands with `--dry`/`-d` if you want to see what the tool does.

## Build Machine

Make sure to have the ssh package installed during the setup and added your SSH key to you an unprivileged user to allow ssh without password.

## Routers

Make sure that you have your key on the router too:
```
configure
set system login user vyos authentication public-keys user@email type 'ssh-rsa'
set system login user vyos authentication public-keys user@email key 'SSH-KEY'
commit
save
```
(Assuming a ssh-rsa, the key `type` is the first word in the line of your SSH key in ./ssh/authorized_keys)


If you are using a VM, you will also need to map the ssh port for remote access.

