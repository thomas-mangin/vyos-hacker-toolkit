#!/usr/bin/env python3

import os
import sys

from vyosextra import log
from vyosextra import cmd
from vyosextra import arguments


class Command(cmd.Command):
	def edit(self, folder):
		editor = self.config.get('global', 'editor')
		self.run(f'{editor} {folder}')

	def branched_repo(self, branch, repo):
		return os.path.join(self.config.get('global', 'working_dir'), branch, repo)



def edit():
	args = arguments.setup(
		'edit vyos code',
		['repository', 'presentation']
	)
	cmds = Command(args.show, args.verbose)
	cmds.edit(cmds.branched_repo(args.branch, args.repository))

if __name__ == '__main__':
	edit()
