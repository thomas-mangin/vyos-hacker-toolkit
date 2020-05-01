Hacking VyOS should be easy, this tools helps with the groundwork.

My day to day machine runs OSX, unfortunately it is not possible to compile the VyOS ISO directly on MacOS (even using Docker - at least until they implement mknod), so I needed a Linux Virtual Machine for it. I also like to have an agreable workflow so I started working on some code to automate my most common tasks, which evolved from a small number of shell script to this python project.

But should you be developing on Linux, setting your build server to 127.0.0.1:22 will cause the program to use the current user on the local machine and will surely make hacking on VyOS easier and more agreable.

So if you need to:
 * build (and test) the VyOS ISO
 * update VyOS to the latest rolling (including using the latest rolling)
 * branch and edit code from your VyOS github repository
 * push codes change to a router

Then read on.

# Quick Installation

The tools can be run directly from the source code folder but it may be easiest to build a zipapp (a self contain python program) from the provided tools and move it in your $PATH.

It can be done as following:
```
git clone git@github.com:thomas-mangin/vyos-extra extra
cd vyos-extra
./release vyos
mv vyos /usr/local/bin/
cp ./etc/vyos-extra.conf.sample /usr/local/etc/vyos-extra.conf
vi /usr/local/etc/vyos-extra.conf
vyos setup build
```

The application can also be installed using `setup.py`, or ran directly from the repository, but until there is a PyPI release, this is not the recommended way.

Then edit `/usr/local/etc/vyos-extra.conf` to configure your build server(s) and router(s).

You should setup one build server (normally called build) where the tools will setup a VyOS development environment, and one router where you can test new image / code change.

While the configuration file is the prefered configuration way, it is also possible to use environment variable (which will take precedence), prepending the name with "VYOS_", and using the same name in upper case.

For example, doing this to change which email get into a VyOS ISO
```
env VYOS_GLOBAL_EMAIL=ci@buiness.com vyos make iso
env VYOS_ROUTER_USER=vyos vyos ssh router
```

# Tools

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

# Setup

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

[router]
role = router
host = 127.0.0.1
port = 2200
user = vyos
file = ~/.ssh/mykey
```

# Local setup

On mac, the following tools shoulld installed with [HomeBrew](https://brew.sh)) for the tool to work.
```
brew install git
brew install rsync
```

# Build Machine

The code should work with both Ubuntu or Debian 10. For Debian, please see the wiki on how to install and configure sudo before attempting setup.

Make sure to have the ssh package installed during the setup and add your SSH key to you an unprivileged user to allow ssh without password (once ssh-askpass saved it).

This build tool is still being tested and installing docker may require to reboot the machine and re-run of the command ATM.

# Routers

The virtual box immage is running a normal VyOS image on a VM
 * with the local ssh port mapped for remote access
 * with your ssh key so the tools can ssh without password using ssh-askpass

Assuming a ssh-rsa (the key `type` is the first word in the line of your SSH key in ./ssh/authorized_keys)

```
configure
set system login user vyos authentication public-keys user@email type 'ssh-rsa'
set system login user vyos authentication public-keys user@email key 'SSH-KEY-AS-IN-AUTHORIZED-KEYS'
commit
save
```
