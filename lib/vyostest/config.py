import os
import sys
import glob

class Config(dict):
	def __init__(self, home):
		wd = os.path.abspath(os.path.dirname(sys.argv[0]))
		etc = os.path.join(wd, '..', 'etc', '*')
		self.data = os.path.join(wd, '..', 'data')

		for name in glob.glob(etc):
			with open(name) as f:
				base = os.path.basename(name)
				part = base.split('_', 1)
				if len(part) == 1:
					self[base] = f.readline().strip().replace('$HOME', home)
					continue
				self.setdefault(part[0], {})[part[1]] = f.readline(
				).strip().replace('$HOME', home)

	def readlines(self, name):
		with open(os.path.join(self.data, name)) as f:
			return f.readlines()

	def ssh(self, where, command=''):
		port = self[where]['port']
		user = self[where]['user']
		host = self[where]['host']
		return f'ssh -p {port} {user}@{host} "{command}"'

	def scp(self, where, src, dst):
		port = self[where]['port']
		user = self[where]['user']
		host = self[where]['host']
		return f'scp -r -P {port} {src} {user}@{host}:{dst}'

	def docker(self, repo, command):
		build = self['build']['repo']
		return f'docker run --rm --privileged -v {build}:{build} -w {build}/{repo} vyos/vyos-build:current {command}'

	def rsync(self, src, dest):
		port = self['build']['port']
		user = self['build']['user']
		host = self['build']['host']
		return f'rsync -avh --delete -e "ssh -p {port}" {src} {user}@{host}:{dest}'

	# def rsync_out(self, src, dest):
	# 	port = self['build']['port']
	# 	user = self['build']['user']
	# 	host = self['build']['host']
	# 	dest = remote.replace('$HOME', HOME)
	# 	return f'rsync -a -e "ssh -p {port}" {user}@{host}:{src} {dest}'

	def printf(self, data):
		return 'printf "' + data.replace('\n', '\\n').replace('"', '\"') + '"'
