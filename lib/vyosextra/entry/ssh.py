#!/usr/bin/env python3

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
	control = Control(arg.show, arg.verbose)

	if not config.exists(arg.machine):
		sys.stderr.write(f'machine "{arg.machine}" is not configured\n')
		sys.exit(1)

	connect = config.ssh(arg.machine, '')

	if arg.show or arg.verbose:
		print(connect)
	
	if arg.show:
		return

	print(f'connecting to {arg.machine}')
	fullssh = subprocess.check_output(['which','ssh']).decode().strip()
	os.execvp(fullssh,connect.split())
	log.completed(arg.debug, 'session terminated')


if __name__ == '__main__':
	main()
