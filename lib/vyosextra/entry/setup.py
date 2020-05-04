#!/usr/bin/env python3
# encoding: utf-8

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
			config.printf(config.read('source.list')),
			config.ssh(where, 'cat - > /etc/apt/sources.list.d/vyos-extra.list')
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

	def setup_build(self, where):
		packages = 'qemu-kvm libvirt-clients libvirt-daemon-system git rsync docker.io docker-compose'

		print("Please enter the host root password (it is not saved)")
		print("It is required to setup password-less command via sudo")
		username = config.get(where, 'user')
		if self.dry:
			password = 'your-password'
		else:
			password = getpass('password: ')
			password = f"'{password}'"

		self.ssh(where, f"echo {password} | sudo -S apt-get update", hide=password, exitonfail=False)
		absent = self.ssh(where, f"echo {password} | sudo -S apt-get install sudo", hide=password, exitonfail=False)
		if absent:
			self.ssh(where, f"echo {password} | " + "sudo -S adduser ${USER} sudo", hide=password)

		absent = self.ssh(where, f"echo {password} | sudo -S grep NOPASSWD /etc/sudoers >/dev/null 2>/dev/null", hide=password, exitonfail=False)
		if absent:
			self.ssh(where, f"echo {password} | sudo -S sed -i '$ a\{username} ALL=(ALL) NOPASSWD: ALL' /etc/sudoers 2> /dev/null", hide=password)


		print('updating the OS to make sure the packages are on the latest version')
		print('it may take some time ...')

		self.ssh(where, 'sudo dpkg --configure -a')
		self.ssh(where, f'sudo apt-get --yes upgrade')
		self.ssh(where, f'sudo apt-get --yes --no-install-recommends install {packages}')

		self.ssh(where, f'sudo adduser {username} libvirt')
		# no f-string here in purpose we want ${USER}
		self.ssh(where, 'sudo usermod -aG docker ${USER}')

		# may need reboot ?

		self.ssh(where, 'docker pull vyos/vyos-build:current')

		self.ssh(where, 'mkdir -p ~/vyos')
		self.ssh(where, 'cd ~/vyos/ && test -d vyos-built && git clone https://github.com/vyos/vyos-build.git', exitonfail=False)
		self.ssh(where, 'cd ~/vyos/vyos-build && git pull')
		# self.ssh(where, 'cd ~/vyos/vyos-build && docker build -t vyos-builder docker')


def main():
	'set a machine for this tool'
	arg = arguments.setup(
		__doc__,
		['machine', 'presentation']
	)
	control = Control(arg.dry, arg.quiet)

	if not config.exists(arg.machine):
		sys.exit(f'machine "{arg.machine}" is not configured\n')

	role = config.get(arg.machine, 'role')
	if not role:
		print('the machine "{arg.machine}" is not setup')

	if role == 'router':
		control.setup_router(arg.machine)
	elif role == 'build':
		control.setup_build(arg.machine)
	else:
		log.completed('the machine "{arg.machine}" is not correctly setup')

if __name__ == '__main__':
	main()
