# Setup on Mac

It is not possible to compile VyOS on MacOS, therefore a VM environement need to be used.

This solution is designed with VirtualBox 
(TODO: use vagrant to automate the VM build)

It will be composed of:
  - A build VM (vyos-build) which will be used to build debian packages and iso
  - A test VM (vyos-router) which will be used to check the validity of the code
  - A set of tools to help the transfer the build image from one to the other (this repository)

The different vyos repositories will be placed in a code folder located in ~/Vyos, which will be shared with the build machine on /vyos

# This repository

All the users, IPs and ports can be configured using the variables in `etc`.
The bin folder of this repository should be added to the PATH.

```
mkdir ~/VyOS
cd ~/VyOS
git clone git@github.com:thomas-mangin/vyos-extra vyos-extra
echo "export PATH=$PATH:$HOME/Vyos/vyos-extra/bin" >> ~/.profile
```

## Vyos code folder

Create a Vyos directory which will include all your development

```
cd ~/VyOS
git clone git@github.com:vyos/vyos-1x vyos-1x
```

## Setup SSH

Setup your local `~/.ssh/config` file to include the following hosts, making sure the ssh key does exists
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

# vyos-build

## Base Install

The machine is built using Debian 10, as it is the same based OS vyos is using.
```
cd ~/VyOS
curl https://cdimage.debian.org/debian-cd/current/amd64/iso-cd/debian-10.3.0-amd64-netinst.iso -o debian-10.3.0-amd64-netinst.iso
```

Create a non-administrative user called vyos
Make sure to have the ssh package installed during the setup of
add your SSH key to your user under ~vyos/.ssh/authorized_keys so that you can ssh without password

## Install sudo

```
su -
apt install --yes sudo
adduser vyos sudo
exit
exit
```

## Enable VT-x / AMD-V for KVM

In order to be able to use KVM, go to Settings > System > Processor and tick "Enable Nested VT-x/AMD-V"

## Add VirtualBox guest OS additions

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

## Mount the local vyos development folder to the VM

On the network interface, Host port 127.0.0.1 port 2200 to your Guest VM IP port 22
Also create a "Shared Folder" called VyOS mapping ~/Vyos to /vyos

Then have the system automount the folder
```
echo "vyos		/vyos		vboxsf rw,dev,uid=1000,gid=1000    0       0" >> /etc/fstab
```

## Install Docker

Install Docker
```
sudo apt install --yes git
sudo apt install --yes docker
sudo apt install --yes docker.io
sudo usermod -aG docker ${USER}
```

## Install KVM

```
sudo apt-get install --yes --no-install-recommends qemu-kvm libvirt-clients libvirt-daemon-system
sudo adduser vyos libvirt
```

## Install the vyos-builder container

Using Docker registry
```
docker pull vyos/vyos-build:current
```

Or manual installation
```
mkdir ~/vyos
cd ~/vyos

git clone https://github.com/vyos/vyos-build.git
cd vyos-build/
docker build -t vyos-builder docker
```

# vyos-router

The virtual box immage is running a normal VyOS image 
 * with the local ssh port mapped to 127.0.0.1 port 2201
 * adding your ssh key to a vyos (default) user

Assuming a ssh-rsa (the key type is the first word in the line of your SSH key in ./ssh/authorized_keys)

```
configure
set system login user vyos authentication plaintext-password 'your-password'
set system login user vyos authentication public-keys thomas@mangin.com type 'ssh-rsa'
set system login user vyos authentication public-keys user@email key 'SSH-KEY-AS-IN-AUTHORIZED-KEYS'
commit
save
```

# Tools

There are:
 * vyos-iso <repo-name>, build and test the iso
 * vyos-dpkg <repo-name>, build and install the package on the router
 * vyos-update, copy the most common changed files from vyos-1x to the router (faster than making a debian package)
 * vyos-test, install smoketest on the VM and run it

Only a few files are copied by vyos-update, make sure all your changes are copied across.
