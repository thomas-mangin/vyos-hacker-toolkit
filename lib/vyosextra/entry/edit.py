#!/usr/bin/env python3

import os
import sys

from vyosextra import log
from vyosextra import cmd
from vyosextra import arguments
from vyosextra.config import config


class Command(cmd.Command):
	def edit(self, folder):
		editor = config.get('global', 'editor')
		self.run(f'{editor} {folder}')

	def branched_repo(self, branch, repo):
		return os.path.join(config.get('global', 'working_dir'), branch, repo)



def main():
	'edit vyos code'
	args = arguments.setup(
		__doc__,
		['repository', 'presentation']
	)
	cmds = Command(args.show, args.verbose)
	cmds.edit(cmds.branched_repo(args.branch, args.repository))

if __name__ == '__main__':
	main()
