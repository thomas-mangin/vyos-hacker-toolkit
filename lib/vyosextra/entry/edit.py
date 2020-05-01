#!/usr/bin/env python3

import os
import re
import sys
import argparse

from vyosextra import log
from vyosextra import cmd


class Command(cmd.Command):
	def edit(self, folder):
		editor = self.config.get('global', 'editor')
		self.run(f'{editor} {folder}')

	def branched_repo(self, branch, repo):
		return os.path.join(self.config.get('global', 'working_dir'), branch, repo)


def query_valid_vyos(branch, repository):
	if not re.match('T[0-9]+', branch):
		input('your branch name does not look like a phabricator entry (like T2000)')

	if repository is None:
		repository = '.'
	elif not repository.startswith('vyos-') and not repository.startswith('vyatta-'):
		input('your repository name does not look like a vyos project (like vyos-1x)')


def edit():
	parser = argparse.ArgumentParser(description='edit code')
	parser.add_argument("branch", help='the phabricator/branch to work on')
	parser.add_argument("repository", help='the repository to work on', nargs='?')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	query_valid_vyos(args.branch, args.repository)

	cmds = Command(args.show, args.verbose)
	cmds.edit(cmds.branched_repo(args.branch, args.repository))

if __name__ == '__main__':
	edit()
