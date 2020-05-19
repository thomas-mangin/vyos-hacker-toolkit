#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
from getpass import getpass
from datetime import datetime

from vyosextra import log
from vyosextra import control
from vyosextra import arguments
from vyosextra.config import config


class Control(control.Control):
    def setup_router(self, where):
        # on my local VM which goes to sleep when I close my laptop
        # time can easily get out of sync, which prevent apt to work
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.ssh(where, f"sudo date -s '{now}'")

        self.ssh(where, f'sudo chgrp vyattacfg /etc/apt/sources.list.d')
        self.ssh(where, f'sudo chmod g+rwx /etc/apt/sources.list.d')

        self.chain(
            config.printf(config.read('source.list')), config.ssh(where, 'cat - > /etc/apt/sources.list.d/vyos-extra.list')
        )

        packages = 'vim git ngrep jq gdb strace apt-rdepends rsync'
        self.ssh(where, f'sudo apt-get --yes update')
        # self.ssh(where, f'sudo apt-get --yes upgrade')))
        self.ssh(where, f'sudo apt-get --yes install {packages}')

        self.ssh(where, f'ln -sf /usr/lib/python3/dist-packages/vyos vyos')
        self.ssh(where, f'ln -sf /usr/libexec/vyos/conf_mode conf')
        self.ssh(where, f'ln -sf /usr/libexec/vyos/op_mode op')

        for src, dst in self.move:
            self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
            self.ssh(where, f'sudo chmod -R g+rxw {dst}')

        self.ssh(where, f'touch /config/vyos.ifconfig.debug')
        self.ssh(where, f'touch /config/vyos.developer.debug')
        self.ssh(where, f'touch /config/vyos.cmd.debug')
        self.ssh(where, f'touch /config/vyos.log.debug')

    def _sudo(self, where, password, command, exitonfail=False):
        _, _, r = self.ssh(where, f'echo {password} | sudo -S {command}', hide=password, exitonfail=exitonfail)
        return r

    def setup_build(self, where, with_sudo):
        packages = 'qemu-kvm libvirt-clients libvirt-daemon-system'
        packages += ' git rsync docker.io docker-compose'

        # for crux
        packages += ' apt-transport-https ca-certificates curl'
        packages += ' gnupg2 software-properties-common'

        repo = config.get(where, 'repo')
        repo_name = os.path.basename(repo)
        repo_folder = os.path.dirname(repo)

        _, _, code = self.ssh(where, f"test -d {repo}", exitonfail=False)
        if code == 0:
            print('this machine is already setup')
            return

        if with_sudo:
            print('----')
            print("Please enter the host root password (it is not saved)")
            print("It is required to setup password-less command via sudo")
            username = config.get(where, 'user')
            if self.dry:
                password = 'your-password'
            else:
                password = getpass('password: ')
                password = f"'{password}'"

            print('----')
            print('updating the OS to make sure the packages are on the latest version')
            print('it may take some time ...')
            print('----')
            self._sudo(where, password, 'dpkg --configure -a')
            self._sudo(where, password, 'apt-get --yes upgrade')
            self._sudo(where, password, 'apt-get update', exitonfail=False)

            print('----')
            print('setting up sudo ...')
            print('----')
            if self._sudo(where, password, 'apt-get install sudo', exitonfail=False):
                self._sudo(where, password, 'adduser ${USER} sudo')
            if self._sudo(where, password, 'grep NOPASSWD /etc/sudoers', exitonfail=False):
                sed = f"sed -i '$ a\{username} ALL=(ALL) NOPASSWD: ALL' /etc/sudoers"  # noqa: W605,E501
                self._sudo(where, password, sed)
            else:
                print('sudo is already setup')

        print('----')
        print('installing packages required for building VyOS')
        print('----')

        print('----')
        print('adding keys for debian')
        print('----')
        # crux
        self.ssh(where, 'curl -fsSL https://download.docker.com/linux/debian/gpg | sudo apt-key add -')

        # crux
        # self.ssh(where, 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 7EA0A9C3F273FCD8')
        # self._sudo(where, 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 9D6D8F6BC857C906')
        # self._sudo(where, 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 0E08A149DE57BFBE')
        # self._sudo(where, 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 7638D0442B90D010')
        # self._sudo(where, 'sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 32C249BD0DF04B5C')

        # crux
        self.ssh(where, 'sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/debian $(lsb_release -cs) stable"')
        self.ssh(where, f'sudo apt-get --yes --no-install-recommends install {packages}')  # noqa: E501

        print('----')
        print('adding the right permission to the user')
        print('----')
        self.ssh(where, f'sudo adduser {username} libvirt')
        # no f-string here in purpose we want ${USER}
        self.ssh(where, 'sudo usermod -aG docker ${USER}')

        print('----')
        print('installing VyOS docker build image')
        print('----')
        self.ssh(where, 'sudo systemctl restart docker.service')
        self.ssh(where, 'docker pull vyos/vyos-build:crux', su=True)
        self.ssh(where, 'docker pull vyos/vyos-build:current', su=True)

        print('----')
        print('installing vyos-build')
        print('----')
        self.ssh(where, f'mkdir -p {repo_folder}')
        self.ssh(where, f'rm -rf {repo_folder}/{repo_name}', exitonfail=False)
        self.ssh(
            where,
            f"cd {repo_folder} && " f"test '!' -d vyos-built && " f"git clone https://github.com/vyos/vyos-build.git {repo_name}",
            exitonfail=False,
        )
        self.ssh(where, f'cd {repo} && git pull')
        # self.ssh(where, 'cd ~/vyos/vyos-build && docker build -t vyos-builder docker')

        print('----')
        print("Please logout and log back in if you have installed locally")


def main():
    'set a machine for this tool'
    arg = arguments.setup(__doc__, ['machine', 'presentation'])
    control = Control(arg.dry, arg.quiet)

    if not config.exists(arg.machine):
        sys.exit(f'machine "{arg.machine}" is not configured\n')

    role = config.get(arg.machine, 'role')
    if not role:
        print('the machine "{arg.machine}" is not setup')

    if role == 'router':
        control.setup_router(arg.machine)
    elif role == 'build':
        control.setup_build(arg.machine, arg.sudo)
    else:
        log.completed('the machine "{arg.machine}" is not correctly setup')


if __name__ == '__main__':
    main()
