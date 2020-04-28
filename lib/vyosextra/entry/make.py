#!/usr/bin/env python3

import argparse

from vyosextra import log
from vyosextra import cmd


HOME = '/home/vyos'
LOCATION = 'packages'

def make(what='iso'):
	parser = argparse.ArgumentParser(description='build and install a vyos debian package')
	parser.add_argument('-1', '--vyos', type=str, help='vyos-1x folder to build')
	parser.add_argument('-k', '--smoke', type=str, help="vyos-smoke folder to build")
	parser.add_argument('-c', '--cfg', type=str, help="vyatta-cfg-system folder to build")
	parser.add_argument('-o', '--op', type=str, help="vyatta-op folder to build")

	parser.add_argument('-e', '--extra', type=str, help='extra debian package(s) to install')
	parser.add_argument('-n', '--name', type=str, help='name/tag to add to the build version')
	parser.add_argument('-b', '--backdoor', type=str, help='install an admin account on the iso with this passord')
	parser.add_argument('-f', '--force', help="make without custom package", action='store_true')
	parser.add_argument('-t', '--test', help='test the iso when built', action='store_true')

	parser.add_argument('-7', '--setup', help='setup for use by this program', action='store_true')
	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()
	cmd.DRY = args.show
	cmd.VERBOSE = args.verbose

	cmds = cmd.Command(HOME)

	todo = {
		('vyos-1x', args.vyos),
		('vyos-smoketest', args.smoke),
		('vyatta-cfg-system', args.cfg),
		('vyatta-op', args.op)
	}
	done = False

	if args.setup:
		cmds.setup_router()

	cmds.update_build()
	for package, option in todo:
		if option:
			done = cmds.build(LOCATION, package, option)

	if done or args.force:
		cmds.configure(LOCATION, args.extra, args.name)
		cmds.backdoor(args.backdoor)
		cmds.make(what)

	if what == 'iso' and args.test:
		cmds.make('test')

	log.completed(args.debug,'iso built and tested')


if __name__ == '__main__':
	make('iso')
