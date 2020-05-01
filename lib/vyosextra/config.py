import os
import sys
import glob
import configparser

from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import exists

from vyosextra.insource import read


def absolute_path(*path):
	fname = join(*path)
	for home in ('~/','$HOME/'):
		if fname.startswith(home):
			return abspath(join(os.getenv("HOME"),fname[len(home):]))
	return abspath(fname).replace(' ','\\ ')


class Config(object):
	__default = {
		'global': {
			'store': '/tmp',
			'email': 'no-one@no-domain.com',
			'github': '',
			'editor': 'vi',
			'cloning_dir': '~/vyos/clone',
			'working_dir': '~/vyos',
		},
		'machine': {
			'role': 'router',
			'host': '127.0.0.1',
			'port': '22',
			'user': 'vyos',
			'file': '',
			'repo': '$HOME/vyos/vyos-build',
		},
	}

	conversion = {
		'host':      lambda host: host.lower(),
		'port':      lambda port: int(port),
		'file':      absolute_path,
		'store':     absolute_path,
		'editor':    absolute_path,
		'cloning_dir': absolute_path,
		'working_dir': absolute_path,
	}

	__instance = None
	values = {}

	# This class is a singleton
	def __new__(cls):
		if not cls.__instance:
			cls.__instance = object.__new__(cls)
		return cls.__instance

	def __init__(self):
		self.root = absolute_path(dirname(__file__), '..', '..')
		self.values = {}

		self._read_config()
		self._parse_env()
		self._set_default()

	def _default(self, section, key=None):
		default = self.__default.get(section, {})
		if not default:
			default = self.__default['machine']
		if key is None:
			return default
		return default[key]

	def _conf_file(self, name):
		etcs = ['/etc', '/usr/local/etc']
		if exists(join(self.root, 'lib/vyosextra')):
			etcs = [absolute_path(self.root, 'etc')] + etcs
			etcs = [absolute_path('$HOME', 'etc')] + etcs

		for etc in etcs:
			fname = join(etc,name)
			if exists(fname):
				return fname
		return ''

	def _read_config(self):
		fname = self._conf_file('vyos-extra.conf')
		if not exists(fname):
			return

		config = configparser.ConfigParser()
		config.read(fname)
		for section in config.sections():
			for key in config[section]:
				self.set(section, key, config[section][key])

	def _parse_env(self):
		for env_name in os.environ:
			if not env_name.startswith('VYOS_'):
				continue

			part = env_name.lower().split('_')
			if len(part) != 3:
				continue
			section, key = part[1], part[2]

			if env_value:
				self.set(section, key, value)
				continue

			value = config.get(section, key, fallback=self._default(section,key))
			self.set(option, value)

	def _set_default(self):
		sections = list(self.values)
		sections.append('global')

		for name in set(sections):
			section = self.values.get(name,{})
			default = self._default(name)

			for key in default:
				if key not in section:
					self.set(name, key, self._default(name, key))

	def exists(self, machine):
		return machine in self.values

	def get(self, section, key):
		return self.values.setdefault(section,{}).get(key,'')

	def set (self, section, key, value):
		value = self.conversion.get(key, lambda _: _)(value)
		self.values.setdefault(section,{})[key] = value

	def read(self, name):
		return read(join(self.root, 'data'), name)

	def printf(self, string):
		return 'printf "' + string.replace('\n', '\\n').replace('"', '\"') + '"'

	def ssh(self, where, command='', extra=''):
		host = self.values[where]['host']
		user = self.values[where]['user']
		port = self.values[where]['port']
		role = self.values[where]['role']
		file = self.values[where]['file']

		if file:
			extra += f' -i {file}'

		# optimisation in case we installed / are installing locally
		if role == 'build' and host in ('localhost', '127.0.0.1', '::1') and port == 22:
			return command

		command = command.replace('$', '\$')
		if ' ' in command:
			command = f'"{command}"'

		return f'ssh {extra} -p {port} {user}@{host} {command}'

	def scp(self, where, src, dst):
		host = self.values[where]['host']
		user = self.values[where]['user']
		port = self.values[where]['port']
		role = self.values[where]['role']
		if role == 'build' and host in ('localhost', '127.0.0.1', '::1') and port == 22:
			return f'scp -r {src} {dst}'
		dst = dst.replace('$', '\$')
		return f'scp -r -P {port} {src} {user}@{host}:{dst}'

	def docker(self, where, rwd, command):
		# rwd: relative working directory
		repo = self.values[where]['repo']
		return f'docker run --rm --privileged -v {repo}:{repo} -w {repo}/{rwd} vyos/vyos-build:current {command}'

	def rsync(self, where, src, dest):
		host = self.values[where]['host']
		user = self.values[where]['user']
		port = self.values[where]['port']
		if host in ('localhost', '127.0.0.1', '::1') and port == 22:
			return f'rsync -avh --delete {src} {dest}'
		dest = dest.replace('$', '\$')
		return f'rsync -avh --delete -e "ssh -p {port}" {src} {user}@{host}:{dest}'
