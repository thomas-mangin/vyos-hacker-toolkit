#!/usr/bin/env python3

import os
import sys

from vyosextra import log
from vyosextra import cmd
from vyosextra import config
from vyosextra import arguments
from vyosextra import repository
from vyosextra.repository import InRepo
from vyosextra.config import config


LOCATION = 'compiled'


class Command(cmd.Command):
	def install(self, server, router, location, vyos_repo, folder):
		build_repo = config.get(server,'repo')

		with InRepo(os.path.join(folder,vyos_repo)) as debian:
			package = debian.package(vyos_repo)
			if not package:
				log.failed(f'could not find {vyos_repo} package name')
			if not self.dry:
				log.report(f'installing {package}')

		self.chain(
			config.ssh(server, f'cat {build_repo}/{location}/{package}'),
			config.ssh(router, f'cat - > {package}')
		)
		self.ssh(router, f'sudo dpkg -i --force-all {package}')
		self.ssh(router, f'rm {package}')



def main():
	'build and install a vyos debian package'
	args = arguments.setup(
		__doc__, 
		['server', 'router', 'package', 'presentation']
	)
	cmds = Command(args.show, args.verbose)

	if not config.exists(args.server):
		sys.stderr.write(f'machine "{args.server}" is not configured\n')
		sys.exit(1)

	if not config.exists(args.router):
		sys.stderr.write(f'machine "{args.router}" is not configured\n')
		sys.exit(1)

	role = config.get(args.server, 'role')
	if role != 'build':
		sys.stderr.write(f'target "{args.server}" is not a build machine\n')
		sys.exit(1)

	role = config.get(args.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{args.router}" is not a VyOS router\n')
		sys.exit(1)

	cmds.update_build(args.server)
	for package in args.packages:
		cmds.build(args.server, LOCATION, package, args.location)
		cmds.install(args.server, args.router, LOCATION, package, args.location)

	log.completed(args.debug, 'package(s) installed')


if __name__ == '__main__':
	main()
