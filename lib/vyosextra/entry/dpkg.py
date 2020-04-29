#!/usr/bin/env python3

import sys
import argparse

from vyosextra import log
from vyosextra import cmd
from vyosextra import config
from vyosextra import repository
from vyosextra.repository import InRepo


LOCATION = 'compiled'


class Command(cmd.Command):
	def install(self, server, router, location, vyos_repo, folder):
		build_repo = self.config.values[server]['repo']

		with InRepo(folder) as debian:
			package = debian.package(vyos_repo)
			if not package:
				log.failed(f'could not find {vyos_repo} package name')
			if not self.dry:
				log.report(f'installing {package}')

		self.chain(
			self.config.ssh(server, f'cat {build_repo}/{location}/{package}'),
			self.config.ssh(router, f'cat - > {package}')
		)
		self.ssh(router, f'sudo dpkg -i --force-all {package}')
		self.ssh(router, f'rm {package}')



def dpkg():
	parser = argparse.ArgumentParser(description='build and install a vyos debian package')
	parser.add_argument("server", help='server on which the action will be performed')
	parser.add_argument("router", help='router on which the packages will be installed')

	parser.add_argument('-1', '--vyos', type=str, help='vyos-1x folder to build')
	parser.add_argument('-k', '--smoke', type=str, help="vyos-smoke folder to build")
	parser.add_argument('-c', '--cfg', type=str, help="vyatta-cfg-system folder to build")
	parser.add_argument('-o', '--op', type=str, help="vyatta-op folder to build")

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)

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

	cmds.update_build(args.server)
	for package, option in todo:
		if option:
			cmds.build(args.server, LOCATION, package, option)
			cmds.install(args.server, args.router, LOCATION, package, option)

	log.completed(args.debug, 'package(s) installed')


if __name__ == '__main__':
	dpkg()
