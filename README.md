"vyos-extra" is my toolset to build and test VyOS. It is shared with the hope it can make building VyOS easier for all

# Tools

There are:
| Command     | Description |
| ---         | --- |
| vyos update | copy the most common changed files from vyos-1x to the router
| vyos dpkg   | build and install the package on a router
| vyos iso    | build a vyos rolling ISO (and possibly test it)
| vyos test   | perform some test on the VM

Only a few files are copied by `vyos update`, make sure all your changes are copied across.

It relies on a working linux build maching (locally or accessed via SSH), and installed VyOS router to test changes.

# Setup

The tools were created as it is not possible to compile VyOS directly MacOS (even using Docker), therefore a VM environement neededs to be used.
Any VM platform can be used, including local KVM.
The tools can also use a native Linux desktop/server, but if it is not possible.

This solution was initially designed with VirtualBox, but due to the lack of support for KVM a genuine Linux server or VM is recommended as otherwise you will not be able to test the VyOS ISO you are generating. It is however be possible to build VyOS on VirtualBox.

This document explains how to setup a development environment composed of:
  - A build VM (vyos-build) which will be used to build debian packages and iso
  - A router VM (vyos-router) which will be used to check the validity of the code
  - And this repository


# Expectations

For the purpose of this document, we will assume that you will perform your development on a Unix like machine (OSX, BSD, Linux, ..) in a `~/vyos` folder, but the tools could be configured to be installed elsewhere. The folder `~/vyos/1x` will contain the cloned repositories, one folder per clone.

The expected workflow include the creation of one repository per Phabricator entry you want to work on (perhaps calling the folder by the name of the phabricator task you are working on.

It is expected that you will fork the vyos-1x repository under your own github account and use this repository for development. It is suggested to add a reference to the original repository with the name "upstream" using `git remote add`.


# Local setup

For performance rsync is used to transfer files between hosts.

On mac, they can be installed with [HomeBrew](https://brew.sh))
```
brew install git
brew install rsync
```

Making the VyOS folders
```
mkdir -p ~/vyos/1x
```

Installing this repository from github
```
cd ~/vyos/
git clone git@github.com:thomas-mangin/vyos-extra extra
```

The `bin` folder of this repository could/should be added to the PATH, it can be done by hand:
```
source ~/vyos/extra/shell/bashrc
```
and adding this file at the end of `~/.profile`

All the users, IPs and ports used to connect to the VM can be configured using the file in
the `etc` folder. Each file contain the value of the variable with the name of the file.

it is also possible to use environment variable, prepending the name with "VYOS_",
and using the same name in upper case. For example (export VYOS_BUILD_HOST=127.0.0.1)

Some helpers aliases are present in the shell folder and can be enabled using for example:
``` 
source ~/vyos/extra/shell/bashrc
```

You can also setup your local `~/.ssh/config` file to include the VM hosts, making sure the ssh key does exists
For example:
```
cat <EOF >> ~/.ssh/config

Host vyos-build
        HostName 127.0.0.1
        User vyos
        Port 2200
        IdentityFile ~/.ssh/id_rsa.personal

Host vyos-router
        HostName 127.0.0.1
        User vyos
        Port 2201
        IdentityFile ~/.ssh/id_rsa.personal
EOF
```
It will allow you to ssh using the name `vyos-build` and `vyos-router`

Finally, clone the vyos-1x project
```
cd ~/vyos/1x
git clone git@github.com:vyos/vyos-1x vyos-1x
```

The shell scripts provided can the use this repository to make copies of it and auto-create branches for you.

# vyos-build VM

Should you run Linux and want to use your local machine for the build system, instead of running a VM.
You can set the build_host to 127.0.0.1/localhost and the port to 22. The tools will then not call
ssh but run the commands on the local machine.

## Base Install

The machine is built using Debian 10, as it is the same based OS vyos is using.
```
cd ~/vyos
curl https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-10.3.0-amd64-netinst.iso -o debian-10.3.0-amd64-netinst.iso
```

Create a non-administrative user called vyos
Make sure to have the ssh package installed during the setup of
add your SSH key to your user under ~vyos/.ssh/authorized_keys so that you can ssh without password

## Install sudo

```
su -
apt install --yes sudo
adduser ${USER} sudo
exit
exit
```

## Enabling  KVM

At the time of writing, it does not work on virtual. So qemu will be slllooowww and this prevent the testing of the ISO.
https://forums.virtualbox.org/viewtopic.php?f=3&t=97035

Attempted with:
VirtualBox: Settings > System > Processor and tick "Enable Nested VT-x/AMD-V"

```
sudo apt-get install --yes --no-install-recommends qemu-kvm libvirt-clients libvirt-daemon-system
sudo adduser vyos libvirt
```

## Install git, rsync and docker

Install Docker
```
sudo apt install --yes git
sudo apt install --yes rsync
sudo apt install --yes docker.io
sudo usermod -aG docker ${USER}
reboot
```

## Install the vyos-builder container

Using Docker registry
```
docker pull vyos/vyos-build:current
```

Or manual installation (ATM, it will require editing the scripts to use this image)
```
mkdir ~/vyos
cd ~/vyos

git clone https://github.com/vyos/vyos-build.git
cd vyos-build/
docker build -t vyos-builder docker
```

## VirtualBox specifics

If you are running VirtualBox, you should/can also do the following:

### Add VirtualBox guest OS additions

running debian 10 with virtual box integration tool installed
Download VboxGuestAditions.iso on your mac and mount it on the VM CDROM
```
latest=$( curl https://download.virtualbox.org/virtualbox/LATEST.TXT )
curl https://download.virtualbox.org/virtualbox/$latest/VBoxGuestAdditions_$latest.iso -o VBoxGuestAdditions.iso
```

```
sudo apt install build-essential dkms linux-headers-$(uname -r)
mount /media/cdrom
sudo /mnt/media/VBoxLinuxAdditions.run
reboot
```

### Mount the local vyos development folder to the VM

On the network interface, Host port 127.0.0.1 port 2200 to your Guest VM IP port 22
Also create a "Shared Folder" called VyOS mapping ~/vyos (on your machine) to /vyos (on the VM)

Then have the system automount the folder
```
echo "vyos		/vyos		vboxsf rw,dev,uid=1000,gid=1000    0       0" >> /etc/fstab
```


# vyos-router

The virtual box immage is running a normal VyOS image 
 * with the local ssh port mapped to 127.0.0.1 port 2201
 * adding your ssh key to a vyos (default) user

Assuming a ssh-rsa (the key type is the first word in the line of your SSH key in ./ssh/authorized_keys)

```
configure
set system login user vyos authentication plaintext-password 'your-password'
set system login user vyos authentication public-keys user@email type 'ssh-rsa'
set system login user vyos authentication public-keys user@email key 'SSH-KEY-AS-IN-AUTHORIZED-KEYS'
commit
save
```
