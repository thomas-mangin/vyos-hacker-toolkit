#!/usr/bin/env python3

import os
import sys
import argparse
from datetime import datetime

from vyosextra import log
# from vyosextra import cmd
from vyosextra.entry import edit


class Command(edit.Command):
	def make(self, directory):
		if self.verbose or self.dry:
			sys.stdout.write(f'making {directory}: ')
		if self.dry:
			return
		if not os.path.exists(directory):
			os.makedirs(directory)

	def dir(self, directory):
		if self.verbose or self.dry:
			sys.stdout.write(f'cd to {directory}: ')
		if not self.dry:
			os.chdir(directory)

	def setup_source(self, repo):
		cloning = self.config.get('global', 'cloning_dir')
		working = os.path.join(cloning, repo)
		user = self.config.get('global', 'github')

		if not os.path.exists(working):
			self.make(cloning)
			self.dir(cloning)
			self.run(f'git clone git@github.com:{user}/{repo}')
			self.dir(working)
			self.run(f'git remote add upstream git://github.com/vyos/{repo}')

		branch = 'current'
		if repo in ('vyos-smoketest',):
			branch = 'master'
		self.make(working)
		self.dir(working)
		self.run(f'git pull upstream {branch}')
		self.run(f'git push origin {branch}')

	def setup_branch(self, branch, repo):
		cloning = os.path.join(self.config.get('global', 'cloning_dir'), repo)
		folder = os.path.join(self.config.get('global', 'working_dir'), branch)
		working = os.path.join(folder, repo)

		if not os.path.exists(working):
			self.make(folder)
			self.run(f'cp -a {cloning} {repo}')

		self.dir(working)
		self.run(f'git checkout -b {branch}')


def branch():
	parser = argparse.ArgumentParser(description='edit code')
	parser.add_argument("branch", help='the phabricator/branch to work on')
	parser.add_argument("repository", help='the repository to work on')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')
	parser.add_argument('-e', '--edit', help='start editor once branched', action='store_true')

	args = parser.parse_args()
	edit.query_valid_vyos(args.branch, args.repository)

	cmds = Command(args.show, args.verbose)
	cmds.setup_source(args.repository)
	cmds.setup_branch(args.branch, args.repository)

	if args.edit:
		cmds.edit(cmds.branched_repo(args.branch, args.repository))

if __name__ == '__main__':
	branch()
