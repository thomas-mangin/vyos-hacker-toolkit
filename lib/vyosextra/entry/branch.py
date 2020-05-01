#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime

from vyosextra import log
# from vyosextra import cmd
from vyosextra.entry import edit


class Command(edit.Command):
	def make(self, dir):
		if self.verbose or self.dry:
			sys.stdout.write(f'making {dir}: ')
		if not self.dry:
			os.makedirs(dir)

	def dir(self, dir):
		if self.verbose or self.dry:
			sys.stdout.write(f'cd to {dir}: ')
		if not self.dry:
			os.chdir(dir)

	def edit(self, location):
		editor = self.config.get('editor')
		self.run(f'{editor} {location}')

	def inside (self, directory):
		if not os.path.exists(directory):
			self.make(directory)
		self.dir(directory)

	def setup_source(self, repo):
		cloning = self.config.get('global', 'cloning_dir')
		working = os.path.join(cloning, repo)
		user = self.config.get('global', 'github')

		if not os.path.exists(working):
			self.inside(cloning)
			self.run(f'git clone git@github.com:{user}/{repo}')
			self.dir(working)
			self.run(f'git remote add upstream git://github.com/vyos/{repo}')

		branch = 'master'
		if repo == 'vyos-1x':
			branch = 'current'
		self.inside(working)
		self.run(f'git pull upstream {branch}')
		self.run(f'git push origin {branch}')

	def setup_branch(self, repo, phabricator):
		branch = os.path.join(self.config.get('global', 'working_dir'), phabricator)
		working = os.path.join(branch, repo)

		if os.path.exists(working):
			return

		cloning = os.path.join(self.config.get('global', 'cloning_dir'), repo)

		self.inside(branch)
		self.run(f'cp -a {cloning} {repo}')
		self.dir(working)
		self.run(f'git checkout -b {phabricator}')

def branch():
	parser = argparse.ArgumentParser(description='edit code')
	parser.add_argument("repository", help='the repository to work on')
	parser.add_argument("phabricator", help='the phabricator/branch to work on')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')
	parser.add_argument('-e', '--edit', help='start editor once branched', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)
	cmds.setup_source(args.repository)
	cmds.setup_branch(args.repository, args.phabricator)

	if args.edit:
		cmds(args.repository, args.phabricator)

if __name__ == '__main__':
	branch()
