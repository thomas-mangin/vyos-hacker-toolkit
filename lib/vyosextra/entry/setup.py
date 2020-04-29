#!/usr/bin/env python3

import argparse
from datetime import datetime

from vyosextra import log
from vyosextra import cmd


class Command(cmd.Command):
	def setup_router(self, where):
		# on my local VM which goes to sleep when I close my laptop
		# time can easily get out of sync, which prevent apt to work
		now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		self.ssh(where, f"sudo date -s '{now}'")

		self.ssh(where, f'sudo chgrp vyattacfg /etc/apt/sources.list.d')
		self.ssh(where, f'sudo chmod g+rwx /etc/apt/sources.list.d')

		data = ''.join(self.config.readlines('source.list'))
		self.chain(
			self.config.printf(data),
			self.config.ssh(where, 'cat - > /etc/apt/sources.list.d/vyos-extra.list')
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

		self.ssh(where, f'touch /tmp/vyos.ifconfig.debug')
		self.ssh(where, f'touch /tmp/vyos.developer.debug')
		self.ssh(where, f'touch /tmp/vyos.cmd.debug')
		self.ssh(where, f'touch /tmp/vyos.log.debug')

	def setup_build(self, where):
		# on my local VM which goes to sleep when I close my laptop
		# time can easily get out of sync, which prevent apt to work
		now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		self.ssh(where, f"sudo date -s '{now}'")

		packages = 'qemu-kvm libvirt-clients libvirt-daemon-system git rsync docker.io'
		self.ssh(where, f'sudo apt-get --yes update')
		self.ssh(where, f'sudo apt-get --yes upgrade')
		self.ssh(where, f'sudo apt-get --yes --no-install-recommends install {packages}')

		self.ssh(where, 'sudo adduser vyos libvirt')
		self.ssh(where, 'sudo usermod -aG docker ${USER}')

		self.ssh(where, 'docker pull vyos/vyos-build: current')

		self.ssh(where, 'mkdir ~/vyos')
		self.ssh(where, 'cd ~/vyos/ && git clone https://github.com/vyos/vyos-build.git')
		# self.ssh(where, 'cd ~/vyos/vyos-build && docker build -t vyos-builder docker')


def setup():
	parser = argparse.ArgumentParser(description='set a machine for this tool')
	parser.add_argument("machine", help='machine on which the action will be performed')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)

	role = cmds.config.get(args.machine,'role')
	if not role:
		print('the machine "{args.machine}" is not setup')

	if role == 'router':
		cmds.setup_router(args.machine)
	elif role == 'build':
		cmds.setup_build(args.machine)
	else:
		print('the machine "{args.machine}" is not correctly setup')


if __name__ == '__main__':
	setup()
