#!/usr/bin/env python3
# encoding: utf-8

import os
import time
import sys

from vyosextra import log
from vyosextra import control
from vyosextra import arguments

from vyosextra.repository import Repository
from vyosextra.config import config


class Control(control.Control):
    def permission(self, where, folder):
        user = config.get(where, 'user')
        with Repository(folder, verbose=self.verbose):
            for src, dst in self.move:
                self.ssh(where, f'sudo chown -R {user} {dst}')
                self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
                self.ssh(where, f'sudo chmod -R g+rxw {dst}')

    def rsync(self, where, folder):
        with Repository(folder, verbose=self.verbose):
            for src, dst in self.move:
                self.run(config.rsync(where, src, dst, exclude='**__pycache__'))

    # there is no portable way, and python only to use inotify / etc.
    def update(self, where, folder):
        files = [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser(folder)) for f in fn]
        modified = dict((f, os.path.getmtime(f)) for f in files if os.path.exists(f))
        while True:
            new_files = [os.path.join(dp, f) for dp, dn, fn in os.walk(os.path.expanduser(folder)) for f in fn]
            new_modified = dict((f, os.path.getmtime(f)) for f in new_files if os.path.exists(f))

            if new_modified != modified:
                modified = new_modified
                self.rsync(where, folder)

            time.sleep(2)


def main():
    'update a VyOS router filesystem with newer vyos-1x code'
    arg = arguments.setup(__doc__, ['update'])
    control = Control(arg.dry, not arg.quiet)

    if not config.exists(arg.router):
        sys.exit(f'machine "{arg.router}" is not configured\n')

    role = config.get(arg.router, 'role')
    if role != 'router':
        sys.exit(f'target "{arg.router}" is not a VyOS router\n')

    control.permission(arg.router, arg.working)
    control.rsync(arg.router, arg.working)
    control.update(arg.router, arg.working)


if __name__ == '__main__':
    main()
