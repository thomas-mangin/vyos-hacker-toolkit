#!/usr/bin/env python3

import os
import argparse

from vyosextra import log

from vyosextra.cmd import Command

LOCATION = 'packages'


def ssh():
	parser = argparse.ArgumentParser(description='ssh to a machine')
	parser.add_argument("machine", help='machine on which the action will be performed')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)
	connect = cmds.config.ssh(args.machine, '')

	if args.show or args.verbose:
		print(connect)
	
	if args.show:
		return

	os.system(connect)
	log.completed(args.debug, 'session terminated')


if __name__ == '__main__':
	ssh()
