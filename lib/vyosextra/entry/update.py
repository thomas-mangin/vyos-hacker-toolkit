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
    timed = []
    def permission(self, where, folder):
        with Repository(folder, verbose=self.verbose):
            for src, dst in self.move:
                self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
                self.ssh(where, f'sudo chmod -R g+rxw {dst}')

    def rsync(self, where, folder):
        with Repository(folder, verbose=self.verbose):
            for src, dst in self.move:
                self.run(config.rsync(where, src, dst))

	
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
    while True:
        time.sleep(0.2)
        control.rsync(arg.router, arg.working)


if __name__ == '__main__':
    main()
