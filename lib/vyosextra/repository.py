import os
import re

from vyosextra import log


class InRepo:
	def __init__(self, folder):
		self.folder = folder
		try:
			self.pwd = os.getcwd()
		except FileNotFoundError:
			log.failed('the folder we were into was deleted')

	def __enter__(self):
		try:
			os.chdir(self.folder)
			return self
		except Exception as e:
			log.failed(f'could not get into the repositoy {self.folder}\n{str(e)}')

	def __exit__(self, rtype, rvalue, rtb):
		os.chdir(self.pwd)

	def package(self, repo):
		with open(os.path.join('debian', 'changelog')) as f:
			line = f.readline().strip()
		found = re.match('[^(]+\((.*)\).*', line)
		if found is None:
			return ''
		version = found.group(1)
		return f'{repo}_{version}_all.deb'

