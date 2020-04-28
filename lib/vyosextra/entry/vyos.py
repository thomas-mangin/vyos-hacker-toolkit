#!/usr/bin/env python3
# encoding: utf-8

import sys

from vyosextra.entry.download import download
from vyosextra.entry.update import update
from vyosextra.entry.dpkg import dpkg
from vyosextra.entry.make import make
from vyosextra.entry.test import test

def help():
	print(f"""\
usage: vyos [-h] COMMAND [COMMAND options]

helper functions for vyos, OPTIONS are:
  update                update a VyOS router with vyos-1x
  dpkg                  build a VyOS package (vyos-1x, ...)
  iso                   build a VyOS iso image
  test                  test a VyOS router

optional arguments:
  -h, --help            show this help message and exit
""")
	sys.exit(0)


def make_sys(extract=0, help=True):
	prog = sys.argv[0]
	cmd = sys.argv[1]
	sys.argv = sys.argv[1:]

	if extract and len(sys.argv) >= extract:
		extracted = sys.argv[:extract]
		sys.argv = sys.argv[extract:]
	else:
		extracted = []

	sys.argv = [f'{prog}-{cmd}'] + sys.argv[1:]

	if help and len(sys.argv) == 1:
		sys.argv.append('-h')

	return extracted

def vyos():
	usage = len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help', 'help')

	if usage:
		help()

	command = sys.argv[1]

	if command == 'update':
		make_sys()
		update()
		return

	if command == 'dpkg':
		make_sys()
		dpkg()
		return

	if command in ('make',):
		target = make_sys(extract=1, help=False)
		if target:
			make(target[0])
			return

	if command in ('iso',):
		make_sys()
		make(command)
		return

	if command == 'download':
		make_sys(help=False)
		download()
		return

	if command == 'test':
		make_sys()
		test()
		return

	help()


if __name__ == '__main__':
	vyos()
