import os
import sys
import glob

class Config(object):
	default = {
		'build_folder':    '/vyos',
		'build_host':      '127.0.0.1',
		'build_port':      '22',
		'build_repo':      '$HOME/vyos/vyos-build',
		'build_user':      'vyos',
		'email':           'no-one@no-domain.com',
		'local_folder':    '$HOME/VyOS',
		'router_host':     '127.0.0.2',
		'router_port':     '22',
		'router_user':     'vyos',
	}

	description = {
		'build_folder':    '...',
		'build_host':      'the build server hostname or IP',
		'build_port':      'the build server ssh port',
		'build_repo':      'location of the vyos-build repository',
		'build_user':      'the build server ssh user',
		'email':           'no-one@no-domain.com',
		'local_folder':    '...',
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

		for option in self.default:
			env_name = f'VYOS_{option.upper()}'
			env_value = os.environ.get(env_name, '')
			if env_value:
				self.set(option, env_value, home)
				continue

			file_name = os.path.join(self.etc, option)
			if not os.path.exists(file_name):
				continue

			with open(file_name) as f:
				self.set(option, f.readline(), home)

	def set (self, option, value, home):
		value = value.strip().replace('$HOME', home)
		self.values[option] = value

	def readlines(self, name):
		with open(os.path.join(self.data, name)) as f:
			return f.readlines()

	def printf(self, string):
		return 'printf "' + string.replace('\n', '\\n').replace('"', '\"') + '"'

	def ssh(self, where, command=''):
		port = self.values[f'{where}_port']
		user = self.values[f'{where}_user']
		host = self.values[f'{where}_host']
		return f'ssh -p {port} {user}@{host} "{command}"'

	def scp(self, where, src, dst):
		port = self.values[f'{where}_port']
		user = self.values[f'{where}_user']
		host = self.values[f'{where}_host']
		return f'scp -r -P {port} {src} {user}@{host}:{dst}'

	def docker(self, repo, command):
		build = self.values['build_repo']
		return f'docker run --rm --privileged -v {build}:{build} -w {build}/{repo} vyos/vyos-build:current {command}'

	def rsync(self, src, dest):
		port = self.values['build_port']
		user = self.values['build_user']
		host = self.values['build_host']
		return f'rsync -avh --delete -e "ssh -p {port}" {src} {user}@{host}:{dest}'
