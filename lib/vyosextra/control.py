import os
import sys
import fcntl

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

	def _report(self, popen):
		def _non_blocking(output):
			fd = output.fileno()
			fl = fcntl.fcntl(fd, fcntl.F_GETFL)
			fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

		def _read(output):
			try:
				return output.read().decode()
			except:
				return ""

		_non_blocking(popen.stdout)
		_non_blocking(popen.stderr)

		result = {1:'', 2:''}

		# (1, popen.stdout, sys.stdout, lambda _: _),
		# (2, popen.stderr, sys.stderr, self._unprefix)):

		while popen.poll() is None:
			for fno, pipe, std, formater in (
				(1, popen.stdout, sys.stdout, lambda _:_),
				(2, popen.stderr, sys.stderr, lambda _:_)):
				recv = _read(pipe)
				if not recv:
					continue

				short = recv
				# short = formater(recv)
				# if not short:
				# 	continue

				log.answer(short)
				result[fno] += short
				if self.verbose:
					std.write(short)

		return result.values()

	def _check(self, code, exitonfail=True):
		if code and exitonfail:
			log.answer(f'returned code {code}')
			log.failed('could not complete action requested')

	def run(self, cmd, ignore='', hide='', exitonfail=True):
		command = f'{cmd}'
		secret = command.replace(hide, '********') if hide else command
		log.command(secret)

		if self.dry or self.verbose:
			print(secret)
		if self.dry:
			return ''

		popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
		out, err = self._report(popen)
		code = popen.returncode
		self._check(code, exitonfail)
		return out, err, code

	def communicate(self, cmd, ignore='', exitonfail=True):
		out, err, code = self._run(cmd, ignore, hide)

		self._check(code, exitonfail=exitonfail)
		return self._report(out, err), code

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
		self._check(popen1.returncode)
		self._check(popen2.returncode)
		self._report(*com2)


class Control(Run):
	move = [
				('python/vyos/*', '/usr/lib/python3/dist-packages/vyos/'),
				('src/conf_mode/*', '/usr/libexec/vyos/conf_mode/'),
				('src/op_mode/*', '/usr/libexec/vyos/op_mode/'),
			]

	def ssh(self, where, cmd, ignore='', extra='', hide='', exitonfail=True, quote=True):
		return self.run(config.ssh(where, cmd, extra=extra, quote=quote), ignore=ignore, hide=hide, exitonfail=exitonfail)

	def scp(self, where, src, dst):
		return self.run(config.scp(where, src, dst))
