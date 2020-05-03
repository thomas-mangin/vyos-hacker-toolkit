#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import textwrap
import argparse

from vyosextra.entry import dispatch

def make_sys(extract=0, help=True):
	prog = sys.argv[0]
	cmd = sys.argv[1]
	sys.argv = sys.argv[1:]

	if extract and len(sys.argv) >= extract:
		extracted = sys.argv[:extract]
		sys.argv = sys.argv[extract:]
	else:
		extracted = []

	sys.argv = [f'{prog} {cmd}'] + sys.argv[1:]

	if help and len(sys.argv) == 1:
		sys.argv.append('-h')

	return extracted


def main():
	if os.environ.get('VYOSEXTRA_DEBUG',None) is not None:
		def intercept(dtype, value, trace):
			import traceback
			traceback.print_exception(dtype, value, trace)
			import pdb
			pdb.pm()
		sys.excepthook = intercept

	choices = list(dispatch.keys())
	choices.sort()
	epilog = '\n'.join([f'   {c:<20} {dispatch[c][1]}' for c in choices])

	parser = argparse.ArgumentParser(
		description='vyos extra, the developer tool',
		add_help=False,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog = f'command options:\n{epilog}')
	parser.add_argument('-h', '--help', 
		help='show this help message and exit', 
		action='store_true')
	parser.add_argument('command', 
		help='command to run',
		nargs='?',
        choices=choices)

	args, _ = parser.parse_known_args()

	if not args.command and args.help:
		parser.print_help()
		return

	helping = {
		'download': False,
	}

	if args.command not in dispatch:
		parser.print_help()
		return

	make_sys(help=helping.get(args.command, True))
	dispatch[args.command][0]()


if __name__ == '__main__':
	main()
