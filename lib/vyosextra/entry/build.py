#!/usr/bin/env python3

import os
import sys

from vyosextra import log
from vyosextra import control
from vyosextra import config
from vyosextra import arguments
from vyosextra import repository
from vyosextra.repository import InRepo
from vyosextra.config import config


LOCATION = 'compiled'


class Control(control.Control):
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

	def update_build(self, where):
		build_repo = config.get(where, 'repo')
		self.ssh(where, f'cd {build_repo} && git pull',
                    'Already up to date.'
           )

	def build(self, where, location, vyos_repo, folder):
		build_repo = config.get(where, 'repo')
		self.ssh(where, f'mkdir -p {build_repo}/{location}/{vyos_repo}')

		with InRepo(os.path.join(folder, vyos_repo)) as debian:
			package = debian.package(vyos_repo)
			if not package:
				log.failed(f'could not find {vyos_repo} package version')
			elif not self.dry:
				log.report(f'building package {package}')

			self.run(config.rsync(where, '.', f'{build_repo}/{location}/{vyos_repo}'))
			self.ssh(where, f'rm {build_repo}/{location}/{package} || true')
			self.ssh(where, config.docker(where, f'{location}/{vyos_repo}', 'dpkg-buildpackage -uc -us -tc -b'))

		return True



def main():
	'build and install a vyos debian package'
	arg = arguments.setup(
		__doc__, 
		['server', 'router', 'package', 'presentation']
	)
	control = Control(arg.show, arg.verbose)

	if not config.exists(arg.server):
		sys.stderr.write(f'machine "{arg.server}" is not configured\n')
		sys.exit(1)

	if not config.exists(arg.router):
		sys.stderr.write(f'machine "{arg.router}" is not configured\n')
		sys.exit(1)

	role = config.get(arg.server, 'role')
	if role != 'build':
		sys.stderr.write(f'target "{arg.server}" is not a build machine\n')
		sys.exit(1)

	role = config.get(arg.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{arg.router}" is not a VyOS router\n')
		sys.exit(1)

	control.update_build(arg.server)
	for package in arg.packages:
		control.build(arg.server, LOCATION, package, arg.location)
		control.install(arg.server, arg.router, LOCATION, package, arg.location)

	log.completed(arg.debug, 'package(s) installed')


if __name__ == '__main__':
	main()
