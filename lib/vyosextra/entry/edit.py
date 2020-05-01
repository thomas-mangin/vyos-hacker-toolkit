#!/usr/bin/env python3

import os
import sys
import argparse

from vyosextra import log
from vyosextra import cmd


class Command(cmd.Command):
	def edit(self, repo, phabricator):
		folder = os.path.join(self.config.get('global', 'working_dir'), phabricator, repo)
		editor = self.config.get('global', 'editor')
		self.run(f'{editor} {folder}')

def edit():
	parser = argparse.ArgumentParser(description='edit code')
	parser.add_argument("repository", help='the repository to work on')
	parser.add_argument("phabricator", help='the phabricator/branch to work on')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)
	cmds.edit(args.repository, args.phabricator)

if __name__ == '__main__':
	edit()
