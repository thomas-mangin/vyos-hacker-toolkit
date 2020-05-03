#!/usr/bin/env python3

import sys

from vyosextra import log
from vyosextra import command
from vyosextra import arguments

from vyosextra.repository import InRepo
from vyosextra.config import config


LOCATION = 'compiled'


class Command(command.Command):
	def copy(self, where, location, repo, folder):
		with InRepo(folder) as debian:
			for src, dst in self.move:
				self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
				self.ssh(where, f'sudo chmod -R g+rxw {dst}')
				self.scp(where, src, dst)


def main():
	'update a VyOS router filesystem with newer vyos-1x code'
	args = arguments.setup(
		__doc__,
		['router', 'package', 'presentation']
	)
	cmds = Command(args.show, args.verbose)

	if not config.exists(args.router):
		sys.stderr.write(f'machine "{args.router}" is not configured\n')
		sys.exit(1)

	role = config.get(args.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{args.router}" is not a VyOS router\n')
		sys.exit(1)

	cmds.copy(args.router, LOCATION, args.package, option)

	log.completed(args.debug, 'router updated')
	

if __name__ == '__main__':
	main()
