import os
import sys
import glob

import configparser

class Config(object):
	default = {
		'build_host':      '127.0.0.1',
		'build_port':      '22',
		'build_repo':      '$HOME/vyos/vyos-build',
		'build_user':      'vyos',
		'local_email':     'no-one@no-domain.com',
		'router_host':     '127.0.0.2',
		'router_port':     '22',
		'router_user':     'vyos',
	}

	conversion = {
		'build_host':      lambda host: host.lower(),
		'build_port':      lambda port: int(port),
		'router_host':     lambda host: host.lower(),
		'router_port':     lambda port: int(port),
	}


	description = {
		'build_host':      'the build server hostname or IP',
		'build_port':      'the build server ssh port',
		'build_repo':      'location of the vyos-build repository',
		'build_user':      'the build server ssh user',
		'local_email':     'the email address to use for the VySO ISO',
		'router_host':     'the target vyos router hostname or IP',
		'router_port':     'the target vyos router ssh port',
		'router_user':     'the target vyos router ssh user',
	}

	__instance = None
	values = {}

	# This class is a singleton
	def __new__(cls, home):
		if not cls.__instance:
			cls.__instance = object.__new__(cls)
		return cls.__instance

	def __init__(self, home):
		wd = os.path.abspath(os.path.dirname(sys.argv[0]))
		self.etc = os.path.join(wd, '..', 'etc')
		self.data = os.path.join(wd, '..', 'data')

		config = configparser.ConfigParser()

		fname = self.etc + '/vyos-extra.conf'
		if not os.path.exists(fname):
			self.etc = '/etc'
			fname = self.etc + '/vyos-extra.conf'

		if os.path.exists(fname):
			config.read(fname)

		for option in self.default:
			env_name = f'VYOS_{option.upper()}'
			env_value = os.environ.get(env_name, '')
			if env_value:
				self.set(option, env_value, home)
				continue

			section, key = option.split('_')
			value = config.get(section, key, fallback=self.default[option])
			self.set(option, value, home)

	def set (self, option, value, home):
		value = value.strip().replace('$HOME', home)
		value = self.conversion.get(option, lambda _: _)(value)
		self.values[option] = value

	def readlines(self, name):
		# This is a trick to not rely on the data folder when
		# the application is installed with pip
		try:
			with open(os.path.join(self.data, name)) as f:
				return f.readlines()
		except Exception as OErr:
			try:
				from vyosextra.data import data
				return data[name].split('\n')
			except ImportError:
				raise OErr

	def printf(self, string):
		return 'printf "' + string.replace('\n', '\\n').replace('"', '\"') + '"'

	def ssh(self, where, command=''):
		host = self.values[f'{where}_host']
		user = self.values[f'{where}_user']
		port = self.values[f'{where}_port']
		if where == 'build' and host in ('localhost', '127.0.0.1', '::1') and port == 22:
			return command
		return f'ssh -p {port} {user}@{host} "{command}"'

	def scp(self, where, src, dst):
		host = self.values[f'{where}_host']
		user = self.values[f'{where}_user']
		port = self.values[f'{where}_port']
		if where == 'build' and host in ('localhost', '127.0.0.1', '::1') and port == 22:
			return command
		return f'scp -r -P {port} {src} {user}@{host}:{dst}'

	def docker(self, repo, command):
		build = self.values['build_repo']
		return f'docker run --rm --privileged -v {build}:{build} -w {build}/{repo} vyos/vyos-build:current {command}'

	def rsync(self, src, dest):
		host = self.values['build_host']
		if host in ('localhost', '127.0.0.1', '::1') and port == 22:
			return f'rsync -avh --delete {src} {dest}'
		user = self.values['build_user']
		port = self.values['build_port']
		return f'rsync -avh --delete -e "ssh -p {port}" {src} {user}@{host}:{dest}'
