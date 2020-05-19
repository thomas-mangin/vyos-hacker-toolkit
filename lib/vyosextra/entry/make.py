#!/usr/bin/env python3
# encoding: utf-8

import sys
from datetime import datetime

from vyosextra import log
from vyosextra import arguments
from vyosextra.config import config

from vyosextra.entry import build as control


class Control(control.Control):
    location = 'makeiso'  # packages, is used by crux !

    def make(self, where, release, target):
        self.ssh(where, config.docker(where, release, '', f'sudo make {target}'), extra='-t')

    def backdoor(self, where, password):
        build_repo = config.get(where, 'repo')

        lines = config.read('vyos-iso-backdoor').split('\n')
        location = lines.pop(0).lstrip().lstrip('#').strip()

        if not password:
            self.ssh(where, f"rm {build_repo}/{location}", exitonfail=False)
            self.ssh(where, f"touch {build_repo}/{location}")
            return

        data = ''.join(lines).format(user='admin', password=password)
        self.chain(config.printf(data), config.ssh(where, f'cat - > {build_repo}/{location}'))

    def configure(self, where, release, extra, name):
        email = config.get('global', 'email')

        date = datetime.now().strftime('%Y%m%d%H%M')
        if name:
            version = f'{release}-{name}-{date}'
        else:
            version = f'{release}-{date}'

        configure = f"--build-by {email}"
        # configure += f" --debian-mirror http://ftp.de.debian.org/debian/"
        configure += f" --version {version}"
        configure += f" --build-type release"
        if extra:
            configure += f"  --custom-package '{extra}'"

        self.ssh(where, config.docker(where, release, '', f'git checkout {release}'))
        self.ssh(where, config.docker(where, release, '', f'./configure {configure}'))


def main(target=''):
    'call vyos-build make within docker'

    options = ['server', 'package', 'make', 'presentation']
    if not target:
        options = ['target'] + options

    arg = arguments.setup(__doc__, options)

    if not target:
        target = arg.target
    release = arg.release or 'current'

    control = Control(arg.dry, arg.quiet)

    if not config.exists(arg.server):
        sys.exit(f'machine "{arg.server}" is not configured')

    role = config.get(arg.server, 'role')
    if role != 'build':
        sys.exit(f'target "{arg.server}" is not a build machine')

    control.cleanup(arg.server)
    control.git(arg.server, 'fetch')

    if target == 'test':
        control.make(arg.server, release, 'test')
        return

    done = False
    if not arg.release:
        for package in arg.packages:
            done = control.build(arg.server, package, arg.location)

    if done:
        control.backdoor(arg.server, arg.backdoor)
    if done or arg.release:
        control.configure(arg.server, release, arg.extra, arg.name)
        control.make(arg.server, release, target)

    if target == 'iso' and arg.test:
        control.make(arg.server, release, 'test')

    log.completed('iso built and tested')


if __name__ == '__main__':
    main('iso')
