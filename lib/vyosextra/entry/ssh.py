#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import subprocess

from vyosextra import log
from vyosextra import control
from vyosextra import arguments
from vyosextra.config import config


class Control(control.Control):
    pass


def main():
    'ssh to a configured machine'
    arg = arguments.setup(
        __doc__,
        ['machine', 'presentation']
    )
    control = Control(arg.dry, arg.quiet)

    if not config.exists(arg.machine):
        sys.exit(f'machine "{arg.machine}" is not configured\n')

    connect = config.ssh(arg.machine, '')

    if arg.dry or arg.quiet:
        print(connect)
    
    if arg.dry:
        return

    log.timed(f'connecting to {arg.machine}')
    fullssh = subprocess.check_output(['which','ssh']).decode().strip()
    os.execvp(fullssh,connect.split())
    log.completed('session terminated')


if __name__ == '__main__':
    main()
