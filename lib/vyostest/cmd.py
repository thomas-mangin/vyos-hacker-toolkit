import os
import sys
from subprocess import Popen
from subprocess import PIPE, STDOUT, DEVNULL

from . import log

DRY = False
VERBOSE = False

def _unprefix(s, prefix='Welcome to VyOS'):
	return '\n'.join(_ for _ in s.split('\n') if _ and _ != prefix)


def _popen(p, ignore):
	msg = p.communicate()
	ret = p.returncode
	out = _unprefix(msg[0].decode().strip())
	if VERBOSE:
		sys.stdout.write(log.answer(out))
	err = msg[1]
	if err and VERBOSE:
		sys.stdout.write(log.answer(_unprefix(err.decode().strip())))
	if ret != 0:
		log.failed(f'command returned code {ret}')
	return out, ret


def run(cmd, ignore=''):
	log.command(f'{cmd}')
	if DRY or VERBOSE:
		sys.stdout.write(f'{cmd}\n')
	if DRY:
		return '', 0
	p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
	return _popen(p, ignore)


def chain(cmd1, cmd2, ignore=''):
	log.command(f'{cmd1} | {cmd2}')
	if DRY or VERBOSE:
		sys.stdout.write(f'{cmd1} | {cmd2}\n')
	if DRY:
		return '', 0
	# XXX: warning .. we are not removing SSH greating from p1 !
	# XXX: ssh ... | ssh ... will not work as written
	p1 = Popen(cmd1, stdout=PIPE, stderr=DEVNULL, shell=True)
	p2 = Popen(cmd2, stdin=p1.stdout, stdout=PIPE, stderr=PIPE, shell=True)
	return _popen(p2, ignore)


def check(out, ret):
	if ret != 0:
		log.failed()
