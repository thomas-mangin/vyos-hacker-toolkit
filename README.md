vyos-extra provide a toold to help build and test VyOS.

# Rationale

As it is not possible to compile VyOS directly MacOS (even using Docker), a Linux Virtual Machine is needed
to develop and test on vyos-1x. This tool make some common operation easier:
 * compiling and installing vyox-1x
 * building and testing the VyOS ISO
 * pushing code change to a router
 * updating a router to the latest VyOS image

In the case of a build server (used to compile VyOS) using 127.0.0.1 and port 22,
will skip using SSH and use the local machine, so the tool not require a VM.

# Quick Installation

The tools can be run directly from the source code folder but it may be easiest
to build a zipapp from the provided tools and move it in your $PATH.

```
cd
git clone git@github.com:thomas-mangin/vyos-extra extra
cd vyos-extra
./release vyos
sudo mv vyos /usr/local/bin/
sudo cp ./etc/vyos-extra.conf.sample /etc/vyos-extra.conf
cd ..
rm -rf vyos-extra
```

It can also be installed using `setup.py`.

Then edit `/etc/vyos-extra.conf` to configure your build server(s) and router(s).

it is also possible to use environment variable, prepending the name with "VYOS_",
and using the same name in upper case. For example
```
export VYOS_BUILD_HOST=10.0.0.1
export VYOS_BUILD_HOST=22
export VYOS_GLOBAL_EMAIL=me@home.com
```

# Tools

All the tools are available through the `vyos` entry point, the commands are:

| names     | Description |
| ---       | --- |
| setup     | setup a VyOS machine (build or router) for development.
| ssh       | ssh to a configured server
| download  | download (if required) and cache the lastest VyOS rolling
| dpkg      | build and install a VyOS package (vyos-1x, ...).
| iso       | build a vyos rolling ISO (and possibly test it)
| make      | call other make function than iso
| update    | update a VyOS router with vyos-1x.
| test      | perform some test on the VM


It relies on a working VyOS development environment (locally or accessed via SSH). This can be done by using the the `setup` command for Debian/Ubuntu (only OS supported ATM).

using `-s/--show` will present you with what the tool is going to do without running any command.
```
# ./bin/vyos ssh router --show
ssh  -i /Users/thomas/.ssh/id_rsa.personal -p 2200 vyos@127.0.0.1
```

Using the `update` feature require the router to have been prepared with `setup`.

Note: 
 * Only a few files are copied by `vyos update` make sure all your changes are copied across
 * The syntax of the tools is still changing

# Setup

For the build, any VM platform can be used, including local KVM, it is also possible to use 
The tools can also use a native Linux desktop/server, but if it is not possible.

In the configuration file, create a name for yours hosts and define how to connect to them.
In the case of a build server (used to compile VyOS) using 127.0.0.1 and port 22, will skip using SSH.

This solution was initially designed with VirtualBox, but due to the lack of support for KVM a genuine Linux server or VM is recommended as otherwise you will not be able to test the VyOS ISO you are generating. It is however be possible to build VyOS on VirtualBox.

# Local setup

On mac, the following tools shoulld installed with [HomeBrew](https://brew.sh)) for the tool to work.
```
brew install git
brew install rsync
```

# Build Machine

The machine can be Ubuntu or Debian 10. For Debian, please see the wiki on how to setup sudo.

Create a non-administrative user, matching your configuration file. Make sure to have the ssh package installed during the setup and add your SSH key to your user under ~vyos/.ssh/authorized_keys so that you can ssh without password.

All the following step can also be performed with `vyos setup build` if you called your build machine `build`. This is still being tested and installing docker may require a reboot and re-run of the command.

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
