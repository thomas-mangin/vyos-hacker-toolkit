#!/usr/bin/env python3
# encoding: utf-8

import os
import sys

from vyosextra import log
from vyosextra import arguments

from vyosextra.config import config
from vyosextra.entry import edit as control


class Control(control.Control):
    def make(self, directory):
        if self.verbose or self.dry:
            sys.stdout.write(f'making {directory}: ')
        if self.dry:
            return
        if not os.path.exists(directory):
            os.makedirs(directory)

    def into(self, directory):
        if self.verbose or self.dry:
            sys.stdout.write(f'cd to {directory}: ')
        if not self.dry:
            os.chdir(directory)

    def setup_source(self, repo):
        cloning = config.get('global', 'cloning_dir')
        working = os.path.join(cloning, repo)
        user = config.get('global', 'github')

        if not os.path.exists(working):
            self.make(cloning)
            self.into(cloning)
            self.run(f'git clone git@github.com:{user}/{repo}')
            self.into(working)
            self.run(f'git remote add upstream git://github.com/vyos/{repo}')

        branch = 'current'
        if repo in ('vyos-smoketest',):
            branch = 'master'
        self.make(working)
        self.into(working)
        self.run(f'git checkout {branch}')
        self.run(f'git reset --hard HEAD')
        self.run(f'git pull upstream {branch}')
        self.run(f'git push origin {branch}')

    def setup_branch(self, branch, repo):
        cloning = os.path.join(config.get('global', 'cloning_dir'), repo)
        folder = os.path.join(config.get('global', 'working_dir'), branch)
        working = os.path.join(folder, repo)

        if not os.path.exists(working):
            self.make(folder)
            self.into(folder)
            self.run(f'cp -a {cloning} {repo}')

        self.into(working)
        self.run(f'git checkout -b {branch}')


def main():
    'setup a branch of a vyos repository'
    arg = arguments.setup(__doc__, ['repository', 'presentation', 'edit'])
    control = Control(arg.dry, not arg.quiet)
    control.setup_source(arg.repository)
    control.setup_branch(arg.branch, arg.repository)
    log.completed('build complete')

    if arg.edit:
        control.edit(control.branched_repo(arg.branch, arg.repository))


if __name__ == '__main__':
    main()
