#!/usr/bin/env python3

import sys
import argparse
from datetime import datetime

from vyosextra import log
from vyosextra import cmd
from vyosextra import config


LOCATION = 'packages'


class Command(cmd.Command):
	def make(self, where, target):
		self.ssh(where, self.config.docker(where, '', f'sudo make {target}'))

	def backdoor(self, where, password):
		build_repo = self.config.get(where,'repo')

		lines = self.config.read('vyos-iso-backdoor').split('\n')
		location = lines.pop(0).lstrip().lstrip('#').strip()

		if not password:
			self.ssh("build", f"rm {build_repo}/{location} || true")
			return

		data = ''.join(lines).format(user='admin', password=password)
		self.chain(
			self.config.printf(data),
			self.config.ssh(where, f'cat - > {build_repo}/{location}')
		)

	def configure(self, where, location,  extra, name):
		email = self.config.get('global','email')

		date = datetime.now().strftime('%Y%m%d%H%M')
		name = name if name else 'rolling'
		version = f'1.3-{name}-{date}'

		configure = f"--build-by {email}"
		configure += f" --debian-mirror http://ftp.de.debian.org/debian/"
		configure += f" --version {version}"
		configure += f" --build-type release"
		if extra:
			configure += f"  --custom-package '{extra}'"

		self.ssh(where, self.config.docker(where, '', 'pwd'))
		self.ssh(where, self.config.docker(where, '', f'./configure {configure}'))




def make(target=''):
	parser = argparse.ArgumentParser(description='build and install a vyos debian package')
	if not target:
		parser.add_argument("target", help='make target')
	parser.add_argument("server", help='machine on which the action will be performed')

	parser.add_argument('-1', '--vyos', type=str, help='vyos-1x folder to build')
	parser.add_argument('-k', '--smoke', type=str, help="vyos-smoke folder to build")
	parser.add_argument('-c', '--cfg', type=str, help="vyatta-cfg-system folder to build")
	parser.add_argument('-o', '--op', type=str, help="vyatta-op folder to build")

	parser.add_argument('-e', '--extra', type=str, help='extra debian package(s) to install')
	parser.add_argument('-n', '--name', type=str, help='name/tag to add to the build version')
	parser.add_argument('-b', '--backdoor', type=str, help='install an admin account on the iso with this passord')
	parser.add_argument('-f', '--force', help="make without custom package", action='store_true')
	parser.add_argument('-t', '--test', help='test the iso when built', action='store_true')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	if not target:
		target = args.target

	cmds = Command(args.show, args.verbose)

	if not cmds.config.exists(args.server):
		sys.stderr.write(f'machine "{args.server}" is not configured\n')
		sys.exit(1)

	role = cmds.config.get(args.server, 'role')
	if role != 'build':
		sys.stderr.write(f'target "{args.server}" is not a build machine\n')
		sys.exit(1)

	todo = {
		('vyos-1x', args.vyos),
		('vyos-smoketest', args.smoke),
		('vyatta-cfg-system', args.cfg),
		('vyatta-op', args.op)
	}
	done = False

	cmds.update_build(args.server)
	for package, option in todo:
		if option:
			done = cmds.build(args.server, LOCATION, package, option)

	if done or args.force:
		cmds.configure(args.server, LOCATION, args.extra, args.name)
		cmds.backdoor(args.server, args.backdoor)
		cmds.make(args.server, target)

	if target == 'iso' and args.test:
		cmds.make(args.server, 'test')

	log.completed(args.debug,'iso built and tested')


if __name__ == '__main__':
	make('iso')
