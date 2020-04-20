import os
import sys

from datetime import datetime
from subprocess import Popen
from subprocess import PIPE, STDOUT, DEVNULL

from .config import Config
from .repository import InRepo
from . import log

DRY = False
VERBOSE = False

class Run(object):
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
			string = cls._unprefix(message.decode().strip())
			log.answer(string)
			if VERBOSE:
				print(string)

		if err:
			log.answer(f'returned code {err}')
			log.failed('could not complete action requested')

	@classmethod
	def _run(cls, cmd, ignore=''):
		command = f'{cmd}'
		log.command(command)
		if DRY or VERBOSE:
			print(command)
		if DRY:
			return ''

		popen = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
		com = popen.communicate()
		cls.check(cmd, popen, com)
		return com

	@classmethod
	def run(cls, cmd, ignore=''):
		com = cls._run(cmd, ignore)
		return cls._unprefix(com[0].decode().strip())

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
		if DRY or VERBOSE:
			print(command)
		if DRY:
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
	def __init__(self, home='/home/vyos'):
		self.config = Config(home)

	def ssh(self, where, cmd, ignore=''):
		return self.run(self.config.ssh(where, cmd), ignore)

	def scp(self, where, src, dst):
		return self.run(self.config.scp(src, dst))

	def update_build(self):
		build_repo = self.config.values['build_repo']
		self.ssh('build', f'cd {build_repo} && git pull',
			'Already up to date.'
		)

	def build(self, location, repo, folder):
		build_repo = self.config.values['build_repo']
		self.ssh('build', f'mkdir -p {build_repo}/{location}/{repo}')

		with InRepo(folder) as debian:
			package = debian.package(repo)
			if not package:
				log.failed(f'could not find {repo} package version')
			elif not DRY:
				log.report(f'building package {package}')

			self.run(self.config.rsync('.', f'{build_repo}/{location}/{repo}'))
			self.ssh('build', f'rm {build_repo}/{location}/{package} || true')
			self.ssh('build', self.config.docker(f'{location}/{repo}', 'dpkg-buildpackage -uc -us -tc -b'))

		return True

	def install(self, location, repo, folder):
		build_repo=self.config.values['build_repo']

		with InRepo(folder) as debian:
			package = debian.package(repo)
			if not package:
				log.failed(f'could not find {repo} package name')
			if not DRY:
				log.report(f'installing {package}')

		self.chain(
			self.config.ssh('build', f'cat {build_repo}/{location}/{package}'),
			self.config.ssh('router', f'cat - > {package}')
		)
		self.ssh('router', f'sudo dpkg -i --force-all {package}')
		self.ssh('router', f'rm {package}')
		return True

	def setup_router(self):
		# on my local VM which goes to sleep when I close my laptop
		# time can easily get out of sync, which prevent apt to work
		now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		self.ssh('router', f"sudo date -s '{now}'")

		self.ssh('router', f'sudo chgrp vyattacfg /etc/apt/sources.list.d')
		self.ssh('router', f'sudo chmod g+rwx /etc/apt/sources.list.d')

		data = ''.join(self.config.readlines('source.list'))
		self.chain(
			self.config.printf(data),
			self.config.ssh('router', 'cat - > /etc/apt/sources.list.d/vyos-extra')
		)

		packages = 'vim git ngrep jq gdb strace apt-rdepends rsync'
		self.ssh('router', f'sudo apt-get --yes update')
		# self.ssh('router', f'sudo apt-get --yes upgrade')))
		self.ssh('router', f'sudo apt-get --yes install {packages}')

		self.ssh('router', f'ln -sf /usr/lib/python3/dist-packages/vyos vyos')
		self.ssh('router', f'ln -sf /usr/libexec/vyos/conf_mode conf')
		self.ssh('router', f'ln -sf /usr/libexec/vyos/op_mode op')

		move = [
          ('python/vyos/*', '/usr/lib/python3/dist-packages/vyos/'),
          ('src/conf_mode/*', '/usr/libexec/vyos/conf_mode/'),
          ('src/op_mode/*', '/usr/libexec/vyos/op_mode/'),
        ]

		for src, dst in move:
			self.ssh('router', f'sudo chgrp -R vyattacfg {dst}')
			self.ssh('router', f'sudo chmod -R g+rxw {dst}')

		self.ssh('router', f'touch /tmp/vyos.ifconfig.debug')
		self.ssh('router', f'touch /tmp/vyos.developer.debug')
		self.ssh('router', f'touch /tmp/vyos.cmd.debug')
		self.ssh('router', f'touch /tmp/vyos.log.debug')

		return True

	def copy(self, location, repo, folder):
		with InRepo(folder) as debian:
			for src, dst in move:
				self.ssh('router', f'sudo chgrp -R vyattacfg {dst}')
				self.ssh('router', f'sudo chmod -R g+rxw {dst}')
				self.scp('router', src, dst)

		return True

	def backdoor(self, password):
		build_repo=self.config.values['build_repo']

		lines = self.config.readlines('vyos-iso-backdoor')
		location = lines.pop(0).lstrip().lstrip('#').strip()

		if not password:
			self.ssh("build", f"rm {build_repo}/{location} || true")
			return

		data = ''.join(lines).format(user='admin', password=password)
		self.chain(
			self.config.printf(data),
			self.config.ssh('build', f'cat - > {build_repo}/{location}')
		)

	def configure(self, location,  extra, name):
		email = self.config.values['email']

		date = datetime.now().strftime('%Y%m%d%H%M')
		name = name if name else 'rolling'
		version = f'1.3-{name}-{date}'

		configure = f"--build-by {email}"
		configure += f" --debian-mirror http://ftp.de.debian.org/debian/"
		configure += f" --version {version}"
		configure += f" --build-type release"
		if extra:
			configure += f"  --custom-package '{extra}'"

		self.ssh('build', self.config.docker('', 'pwd'))
		self.ssh('build', self.config.docker('', f'./configure {configure}'))


	def make(self, target):
		self.ssh('build', self.config.docker('', f'sudo make {target}'))
