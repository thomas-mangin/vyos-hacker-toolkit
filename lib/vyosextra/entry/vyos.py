#!/usr/bin/env python3
# encoding: utf-8

import os
import sys
import textwrap
import argparse

from vyosextra.entry.download import download
from vyosextra.entry.update import update
from vyosextra.entry.dpkg import dpkg
from vyosextra.entry.make import make
from vyosextra.entry.test import test
from vyosextra.entry.setup import setup
from vyosextra.entry.ssh import ssh
from vyosextra.entry.upgrade import upgrade


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

	parser = argparse.ArgumentParser(
		description='vyos extra, the developer tool',
		add_help=False,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog = """\
command options:
   setup                 setup a VyOS machine for development.
   ssh                   ssh to a configured server.

   download              download the lastest VyOS image.
   upgrade               download (if required), cache, and serve locally the lastest rolling

   dpkg                  build and install a VyOS package (vyos-1x, ...).
   iso                   build (and possibly test) VyOS iso image.
   update                update a VyOS router with vyos-1x.

   test                  test a VyOS router.
	""")
	parser.add_argument('-h', '--help', 
		help='show this help message and exit', 
		action='store_true')
	parser.add_argument('command', 
		help='command to run',
		nargs='?',
        choices=['download', 'dpkg', 'iso', 'setup', 'ssh', 'test', 'update', 'upgrade'])

	args, _ = parser.parse_known_args()

	if not args.command and args.help:
		parser.print_help()
		return

	if args.command == 'update':
		make_sys()
		update()
		return

	if args.command == 'upgrade':
		make_sys()
		upgrade()
		return

	if args.command == 'dpkg':
		make_sys()
		dpkg()
		return

	if args.command in ('make',):
		target = make_sys()
		make()

	if args.command in ('iso',):
		make_sys()
		make(args.command)
		return

	if args.command == 'download':
		make_sys(help=False)
		download()
		return

	if args.command == 'setup':
		make_sys()
		setup()
		return

	if args.command == 'ssh':
		make_sys()
		ssh()
		return

	if args.command == 'test':
		make_sys()
		test()
		return

	parser.print_help()


if __name__ == '__main__':
	vyos()
