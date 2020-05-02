#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import textwrap
import argparse

from vyosextra.entry.download import download
from vyosextra.entry.update import update
from vyosextra.entry.build import build
from vyosextra.entry.make import make
from vyosextra.entry.test import test
from vyosextra.entry.setup import setup
from vyosextra.entry.ssh import ssh
from vyosextra.entry.upgrade import upgrade
from vyosextra.entry.branch import branch
from vyosextra.entry.edit import edit


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


def vyos():
	if os.environ.get('VYOSEXTRA_DEBUG',None) is not None:
		def intercept(dtype, value, trace):
			import traceback
			traceback.print_exception(dtype, value, trace)
			import pdb
			pdb.pm()
		sys.excepthook = intercept

	dispatch = {
		'update':   (update, 'update a VyOS router with vyos-1x'),
		'upgrade':  (upgrade, 'download (if required), cache, and serve locally the lastest rolling'),
		'build':    (build, 'build and install a VyOS package (vyos-1x, ...)'),
		'make':     (make, 'call vyos-build make within docker'),
		'iso':      (make, 'build (and possibly test) a VyOS iso image'),
		'download': (download, 'download the lastest VyOS image'),
		'setup':    (setup, 'setup a VyOS machine for development'),
		'ssh':      (ssh, 'ssh to a configured server'),
		'branch':   (branch, 'setup a branch for VyOS development'),
		'edit':     (edit, 'start your editor for a branch'),
		'test':     (test, 'test a VyOS router'),
	}

	epilog = '\n'.join([f'   {k:<20} {v[1]}' for (k, v) in dispatch.items()])

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
        choices=dispatch.keys())

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
	vyos()
