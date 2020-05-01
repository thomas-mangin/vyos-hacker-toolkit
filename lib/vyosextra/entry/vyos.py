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
from vyosextra.entry.code import code


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
		'update': update,
		'upgrade': upgrade,
		'dpkg': dpkg,
		'make': make,
		'iso': make,
		'download': download,
		'setup': setup,
		'ssh': ssh,
		'code': code,
		'test': test,
	}

	parser = argparse.ArgumentParser(
		description='vyos extra, the developer tool',
		add_help=False,
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog = """\
command options:
   setup                 setup a VyOS machine for development.
   ssh                   ssh to a configured server.

   code                  setup a branch for VyOS development
   download              download the lastest VyOS image.
   upgrade               download (if required), cache, and serve locally the lastest rolling

   dpkg                  build and install a VyOS package (vyos-1x, ...).
   iso                   build (and possibly test) VyOS iso image.
   make                  call vyos-build make within docker
   update                update a VyOS router with vyos-1x.

   test                  test a VyOS router.
	""")
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
	dispatch[args.command]()


if __name__ == '__main__':
	vyos()
