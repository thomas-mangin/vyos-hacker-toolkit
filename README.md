# Setup on Mac

It is not possible to compile VyOS on MacOS, therefore a VM environement need to be used.
Ideally an host running Linux will be used, but if it is not possible, Virtualbox can be used.

This solution was initially designed with VirtualBox, but due to the lack of support for KVM, a genuine Linux server or VM is recommended as otherwise you will not be able to test the VyOS ISO you are generating.

The development environment will be composed of:
  - A build VM (vyos-build) which will be used to build debian packages and iso
  - A test VM (vyos-router) which will be used to check the validity of the code
  - A set of tools to help the transfer the build image from one to the other (this repository)

The different vyos repositories will be placed in a code folder located in ~/Vyos, which will be shared with the build machine on /vyos

## Expectations

For the purpose of this document, we will assume that you will perform your development on a Unix like machine (OSX, BSD, Linux, ..) in a `~/VyOS` folder. 
This repository will also be assumed to be installed in the `~/VyOS` folder but it could be installed elsewhere.

You could, for example, create one folder per change PR you want to work on (perhaps calling the folder by the name of the phabricator task you are working on, but this document will assume the `~/VyOS` folder is the folder intended to contain the cloned repositories.

# Local setup

We assume you have git and rsync already installed on your system.
On mac, they can be installed with [HomeBrew](https://brew.sh))
```
brew install git
brew install rsync
```

Making the VyOS folder
```
mkdir ~/VyOS
```

Installing from github
```
cd ~/VyOS
git clone git@github.com:thomas-mangin/vyos-extra vyos-extra
```

adding the scripts to your path

All the users, IPs and ports used to connect to the VM can be configured using the variables in `etc`.
The `bin` folder of this repository could/should be added to the PATH.

```
export path='$PATH'
echo "export PATH=$path:$HOME/Vyos/vyos-extra/bin" >> ~/.profile
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
cd ~/VyOS
git clone git@github.com:vyos/vyos-1x vyos-1x
```

# vyos-build VM

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
Also create a "Shared Folder" called VyOS mapping ~/Vyos to /vyos

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

# Tools

There are:
 * vyos-iso <repo-name>, build and test the iso
 * vyos-dpkg <repo-name>, build and install the package on the router
 * vyos-update, copy the most common changed files from vyos-1x to the router (faster than making a debian package)
 * vyos-test, install smoketest on the VM and run it

Only a few files are copied by vyos-update, make sure all your changes are copied across.
