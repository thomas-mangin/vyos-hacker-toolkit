import os
import re

from vyosextra import log


class Repository:
    official = [
        'vyos-1x', 'vyos-cloud-init', 'vyos-salt-minion', 'vyos-world',
        'vyos-xe-guest-utilities', 'vyos-replace', 'vyos-build-frr',
        'vyos-strongswan', 'vyos-opennhrp',
        'vyos-smoketest', 'vyos-documentation',
        'vyatta-op', 'vyatta-cfg', 'vyatta-cfg-system'
    ]

    def __init__(self, folder, verbose=True):
        self.folder = folder
        self.verbose = verbose
        try:
            self.pwd = os.path.abspath(os.getcwd())
        except FileNotFoundError:
            log.failed('the folder we were into was deleted', verbose=verbose)

    def __enter__(self):
        try:
            os.chdir(self.folder)
            return self
        except Exception as e:
            if os.path.basename(self.folder) not in self.official:
                log.failed(
                    f'could not get into the repository {self.folder}\n{str(e)}',
                    verbose=self.verbose
                )
            self.folder = os.path.dirname(self.folder.rstrip('/'))
            return self.__enter__()

    def __exit__(self, rtype, rvalue, rtb):
        os.chdir(self.pwd)

    def package(self, repo):
        with open(os.path.join('debian', 'changelog')) as f:
            line = f.readline().strip()
        found = re.match(r'[^(]+\((.*)\).*', line)
        if found is None:
            return ''
        version = found.group(1)
        return f'{repo}_{version}_all.deb'
