#!/usr/bin/env python3

import sys
import argparse

from vyosextra import log
from vyosextra import cmd
from vyosextra.repository import InRepo


LOCATION = 'compiled'


class Command(cmd.Command):
	def copy(self, where, location, repo, folder):
		with InRepo(folder) as debian:
			for src, dst in self.move:
				self.ssh(where, f'sudo chgrp -R vyattacfg {dst}')
				self.ssh(where, f'sudo chmod -R g+rxw {dst}')
				self.scp(where, src, dst)


def update():
	parser = argparse.ArgumentParser(description='build and install a vyos debian package')
	parser.add_argument('router', help='machine on which the action will be performed')

	parser.add_argument('-1', '--vyos', type=str, help='vyos-1x folder to build')
	parser.add_argument('-k', '--smoke', type=str, help="vyos-smoke folder to build")
	parser.add_argument('-c', '--cfg', type=str, help="vyatta-cfg-system folder to build")
	parser.add_argument('-o', '--op', type=str, help="vyatta-op folder to build")

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)

	if not cmds.config.exists(args.router):
		sys.stderr.write(f'machine "{args.router}" is not configured\n')
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

	for package, option in todo:
		if option:
			cmds.copy(args.router, LOCATION, package, option)

	log.completed(args.debug, 'router updated')
	

if __name__ == '__main__':
	update()
