#!/usr/bin/env python3
# encoding: utf-8

import os
import sys

from vyosextra import log
from vyosextra import control
from vyosextra import arguments
from vyosextra.repository import Repository
from vyosextra.config import config


class Control(control.Control):
    def update_build(self, where):
        build_repo = config.get(where, 'repo')
        self.ssh(where,
                 f'cd {build_repo} && '
                 f'git pull',
                 'Already up to date.')

    def build(self, where, location, vyos_repo, folder):
        build_repo = config.get(where, 'repo')
        self.ssh(where, f'mkdir -p {build_repo}/{location}/{vyos_repo}')

        with Repository(os.path.join(folder, vyos_repo), verbose=self.verbose) as debian:
            package = debian.package(vyos_repo)
            if not package:
                log.failed(f'could not find {vyos_repo} package version', verbose=self.verbose)
            elif not self.dry:
                log.note(f'building package {package}')

            self.run(config.rsync(where, '.', f'{build_repo}/{location}/{vyos_repo}'))
            self.ssh(where, f'rm {build_repo}/{location}/{package}', exitonfail=False)
            self.ssh(where, config.docker(
                where,
                f'{location}/{vyos_repo}', 'dpkg-buildpackage -uc -us -tc -b'))

        return True

    def install(self, server, router, location, vyos_repo, folder):
        build_repo = config.get(server, 'repo')

        with Repository(os.path.join(folder, vyos_repo), verbose=self.verbose) as debian:
            package = debian.package(vyos_repo)
            if not package:
                log.failed(f'could not find {vyos_repo} package name')
            if not self.dry:
                log.note(f'installing {package}')

        self.chain(
            config.ssh(server, f'cat {build_repo}/{location}/{package}'),
            config.ssh(router, f'cat - > {package}')
        )
        self.ssh(router, f'sudo dpkg -i --force-all {package}')
        self.ssh(router, f'rm {package}')


def main():
    'build and install a vyos debian package'
    arg = arguments.setup(
        __doc__,
        ['server', 'router', 'package', 'presentation']
    )
    control = Control(arg.dry, arg.quiet)

    if not config.exists(arg.server):
        sys.exit(f'machine "{arg.server}" is not configured\n')

    if not config.exists(arg.router):
        sys.exit(f'machine "{arg.router}" is not configured\n')

    role = config.get(arg.server, 'role')
    if role != 'build':
        sys.exit(f'target "{arg.server}" is not a build machine\n')

    role = config.get(arg.router, 'role')
    if role != 'router':
        sys.exit(f'target "{arg.router}" is not a VyOS router\n')

    location = 'compiled'

    control.update_build(arg.server)
    for package in arg.packages:
        control.build(arg.server, location, package, arg.location)
        control.install(arg.server, arg.router, location, package, arg.location)
    log.completed('package(s) installed')


if __name__ == '__main__':
    main()
