#!/usr/bin/env python3

import sys
from datetime import datetime

from vyosextra import log
from vyosextra import command
from vyosextra import arguments
from vyosextra.config import config


LOCATION = 'packages'


class Command(command.Command):
	def make(self, where, target):
		self.ssh(where, config.docker(where, '', f'sudo make {target}'))

	def backdoor(self, where, password):
		build_repo = config.get(where,'repo')

		lines = config.read('vyos-iso-backdoor').split('\n')
		location = lines.pop(0).lstrip().lstrip('#').strip()

		if not password:
			self.ssh("build", f"rm {build_repo}/{location} || true")
			return

		data = ''.join(lines).format(user='admin', password=password)
		self.chain(
			config.printf(data),
			config.ssh(where, f'cat - > {build_repo}/{location}')
		)

	def configure(self, where, location,  extra, name):
		email = config.get('global','email')

		date = datetime.now().strftime('%Y%m%d%H%M')
		name = name if name else 'rolling'
		version = f'1.3-{name}-{date}'

		configure = f"--build-by {email}"
		configure += f" --debian-mirror http://ftp.de.debian.org/debian/"
		configure += f" --version {version}"
		configure += f" --build-type release"
		if extra:
			configure += f"  --custom-package '{extra}'"

		self.ssh(where, config.docker(where, '', 'pwd'))
		self.ssh(where, config.docker(where, '', f'./configure {configure}'))


def main(target=''):
	'call vyos-build make within docker'

	options = ['server', 'package', 'make', 'presentation']
	if not target:
		options = ['target'] + options

	arg = arguments.setup(
		__doc__,
		options
	)

	if not target:
		target = arg.target

	cmds = Command(arg.show, arg.verbose)

	if not config.exists(arg.server):
		sys.exit(f'machine "{arg.server}" is not configured')

	role = config.get(arg.server, 'role')
	if role != 'build':
		sys.exit(f'target "{arg.server}" is not a build machine')

	cmds.update_build(arg.server)

	done = False
	for package in arg.packages:
		done = cmds.build(arg.server, LOCATION, package, arg.location)

	if done or arg.force:
		cmds.configure(arg.server, LOCATION, arg.extra, arg.name)
		cmds.backdoor(arg.server, arg.backdoor)
		cmds.make(arg.server, target)

	if target == 'iso' and arg.test:
		cmds.make(arg.server, 'test')

	log.completed(arg.debug,'iso built and tested')


if __name__ == '__main__':
	main('iso')
