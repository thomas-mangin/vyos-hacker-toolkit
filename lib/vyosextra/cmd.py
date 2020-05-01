import os
import sys

from datetime import datetime
from subprocess import Popen
from subprocess import PIPE, STDOUT, DEVNULL

from vyosextra.config import Config
from vyosextra.repository import InRepo
from vyosextra import log


class Run(object):
	dry = False
	verbose = False

	@staticmethod
	def _unprefix(s, prefix='Welcome to VyOS'):
		return '\n'.join(_ for _ in s.split('\n') if _ and _ != prefix)

	@classmethod
	def check(cls, cmd, popen, communicate):
		err = popen.returncode

		# stdout and stderr can be None in case of command error
		for message in (communicate[0], communicate[1]):
			if not message:
				continue
			string = cls._unprefix(message.decode(errors='ignore').strip())
			log.answer(string)
			if string and cls.verbose:
				print(string)

		if err:
			log.answer(f'returned code {err}')
			log.failed('could not complete action requested')

	@classmethod
	def _run(cls, cmd, ignore=''):
		command = f'{cmd}'
		log.command(command)

		if cls.dry or cls.verbose:
			print(command)
		if cls.dry:
			return ''

		popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
		com = popen.communicate()
		cls.check(cmd, popen, com)
		return com

	@classmethod
	def run(cls, cmd, ignore=''):
		com = cls._run(cmd, ignore)
		if com:
			return cls._unprefix(com[0].decode().strip())
		return ''

	@classmethod
	def communicate(cls, cmd, ignore=''):
		com = cls._run(cmd, ignore)
		return (
			cls._unprefix(com[0].decode().strip()),
			com[0].decode().strip(),
		)

	@classmethod
	def chain(cls, cmd1, cmd2, ignore=''):
		command = f'{cmd1} | {cmd2}'
		log.command(command)
		if cls.dry or cls.verbose:
			print(command)
		if cls.dry:
			return ''

		popen1 = Popen(cmd1, stdout=PIPE, stderr=DEVNULL, shell=True)
		popen2 = Popen(cmd2, stdin=popen1.stdout, stdout=PIPE, stderr=PIPE, shell=True)
		# run copopen2.communicate() before popen1.communicate()
		# otherwise there will be no data on the pipe!
	    # as popen1.communicate will have taken it.
		com2 = popen2.communicate()
		com1 = popen1.communicate()
		cls.check(cmd1, popen1, com1)
		cls.check(cmd2, popen2, com2)
		return cls._unprefix(com2[0].decode().strip())


class Command(Run):
	move = [
				('python/vyos/*', '/usr/lib/python3/dist-packages/vyos/'),
				('src/conf_mode/*', '/usr/libexec/vyos/conf_mode/'),
				('src/op_mode/*', '/usr/libexec/vyos/op_mode/'),
			]

	def __init__(self, dry=False, verbose=False):
		Run.dry = dry
		Run.verbose = verbose
		self.config = Config()

	def ssh(self, where, cmd, ignore='', extra=''):
		return self.run(self.config.ssh(where, cmd, extra), ignore)

	def scp(self, where, src, dst):
		return self.run(self.config.scp(where, src, dst))

	def update_build(self, where):
		build_repo = self.config.values[where]['repo']
		self.ssh(where, f'cd {build_repo} && git pull',
			'Already up to date.'
		)

	def build(self, where, location, vyos_repo, folder):
		build_repo = self.config.values[where]['repo']
		self.ssh(where, f'mkdir -p {build_repo}/{location}/{vyos_repo}')

		with InRepo(folder) as debian:
			package = debian.package(vyos_repo)
			if not package:
				log.failed(f'could not find {vyos_repo} package version')
			elif not self.dry:
				log.report(f'building package {package}')

			self.run(self.config.rsync(where, '.', f'{build_repo}/{location}/{vyos_repo}'))
			self.ssh(where, f'rm {build_repo}/{location}/{package} || true')
			self.ssh(where, self.config.docker(where, f'{location}/{vyos_repo}', 'dpkg-buildpackage -uc -us -tc -b'))

		return True

