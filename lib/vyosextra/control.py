import os
import sys

from subprocess import Popen
from subprocess import PIPE, STDOUT, DEVNULL

from vyosextra.config import config
from vyosextra.repository import InRepo
from vyosextra import log


class Run(object):
	def __init__(self, dry, quiet):
		self.dry = dry
		self.verbose = not quiet

	@staticmethod
	def _unprefix(s, prefix='Welcome to VyOS'):
		return '\n'.join(_ for _ in s.split('\n') if _ and _ != prefix)

	def check(self, cmd, popen, communicate):
		err = popen.returncode

		# stdout and stderr can be None in case of command error
		for message in (communicate[0], communicate[1]):
			if not message:
				continue
			string = self._unprefix(message.decode(errors='ignore').strip())
			log.answer(string)
			if string and self.verbose:
				print(string)

		if err:
			log.answer(f'returned code {err}')
			log.failed('could not complete action requested')

	def _run(self, cmd, ignore=''):
		command = f'{cmd}'
		log.command(command)

		if self.dry or self.verbose:
			print(command)
		if self.dry:
			return ''

		popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
		com = popen.communicate()
		self.check(cmd, popen, com)
		return com

	def run(self, cmd, ignore=''):
		com = self._run(cmd, ignore)
		if com:
			return self._unprefix(com[0].decode().strip())
		return ''

	def communicate(self, cmd, ignore=''):
		com = self._run(cmd, ignore)
		return (
			self._unprefix(com[0].decode().strip()),
			com[0].decode().strip(),
		)

	def chain(self, cmd1, cmd2, ignore=''):
		command = f'{cmd1} | {cmd2}'
		log.command(command)
		if self.dry or self.verbose:
			print(command)
		if self.dry:
			return ''

		popen1 = Popen(cmd1, stdout=PIPE, stderr=DEVNULL, shell=True)
		popen2 = Popen(cmd2, stdin=popen1.stdout, stdout=PIPE, stderr=PIPE, shell=True)
		# run copopen2.communicate() before popen1.communicate()
		# otherwise there will be no data on the pipe!
	    # as popen1.communicate will have taken it.
		com2 = popen2.communicate()
		com1 = popen1.communicate()
		self.check(cmd1, popen1, com1)
		self.check(cmd2, popen2, com2)
		return self._unprefix(com2[0].decode().strip())


class Control(Run):
	move = [
				('python/vyos/*', '/usr/lib/python3/dist-packages/vyos/'),
				('src/conf_mode/*', '/usr/libexec/vyos/conf_mode/'),
				('src/op_mode/*', '/usr/libexec/vyos/op_mode/'),
			]

	def ssh(self, where, cmd, ignore='', extra=''):
		return self.run(config.ssh(where, cmd, extra), ignore)

	def scp(self, where, src, dst):
		return self.run(config.scp(where, src, dst))
