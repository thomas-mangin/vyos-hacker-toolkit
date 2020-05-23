import os
import re

from vyosextra import log
from vyosextra import control


class Repository(control.Control):
    official = [
        'vyos-1x',
        'vyos-cloud-init',
        'vyos-salt-minion',
        'vyos-world',
        'vyos-xe-guest-utilities',
        'vyos-replace',
        'vyos-build-frr',
        'vyos-strongswan',
        'vyos-opennhrp',
        'vyos-smoketest',
        'vyos-documentation',
        'vyatta-op',
        'vyatta-cfg',
        'vyatta-cfg-system',
    ]

    def __init__(self, folder, verbose=False):
        control.Control.__init__(self, dry=False, verbose=False)
        self.folder = os.path.abspath(folder)
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
                log.failed(f'could not get into the repository {self.folder}\n{str(e)}', verbose=self.verbose)
            self.folder = os.path.dirname(self.folder.rstrip('/'))
            return self.__enter__()

    def __exit__(self, rtype, rvalue, rtb):
        os.chdir(self.pwd)

    def package(self, repo):
        if not os.path.exists(os.path.join('debian', 'changelog')):
            log.failed(f'Can not find a debian/changelog folder in "{self.folder}"')

        out, _, code = self.run("git describe --tags --long --match 'vyos/*'", exitonfail=False)
        if not out:
            out = "vyos/0.0-no.git.tag"
        return out.replace('vyos/', f'{repo}_').replace('-dirty', '+dirty') + '_all.deb'
