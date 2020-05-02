#!/usr/bin/env python3

import sys

from vyosextra import log
from vyosextra import cmd
from vyosextra import config
from vyosextra import arguments
from vyosextra import repository
from vyosextra.repository import InRepo


LOCATION = 'compiled'


class Command(cmd.Command):
	def install(self, server, router, location, vyos_repo, folder):
		build_repo = self.config.get(server,'repo')

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
	args = arguments.setup(
		'build and install a vyos debian package', 
		['server', 'router', 'presentation']
	)
	cmds = Command(args.show, args.verbose)

	if not cmds.config.exists(args.server):
		sys.stderr.write(f'machine "{args.server}" is not configured\n')
		sys.exit(1)

	if not cmds.config.exists(args.router):
		sys.stderr.write(f'machine "{args.router}" is not configured\n')
		sys.exit(1)

	role = cmds.config.get(args.server, 'role')
	if role != 'build':
		sys.stderr.write(f'target "{args.server}" is not a build machine\n')
		sys.exit(1)

	role = cmds.config.get(args.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{args.router}" is not a VyOS router\n')
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
