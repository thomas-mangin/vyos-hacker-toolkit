import re
import argparse

from vyosextra.register import Registerer
from vyosextra.config import config


register = Registerer()


def setup(description, options, strict=True):
    parser = argparse.ArgumentParser(description=description)
    for option in options:
        register.call(option, parser)

    # oops, another pdb built-in name :p
    arg = [parser.parse_args()] if strict else parser.parse_known_args()

    if 'repository' in options:
        _query_valid_vyos(arg[0].branch, arg[0].repository)
    return arg[0]


def _query_valid_vyos(branch, repository):
    if not re.match('T[0-9]+', branch):
        input('your branch name does not look like a phabricator entry (like T2000)')

    if repository is None:
        repository = '.'
    elif not repository.startswith('vyos-') and not repository.startswith('vyatta-'):
        input('your repository name does not look like a vyos project (like vyos-1x)')


# posistional options

def _branch(parser):
    parser.add_argument('branch', help='the phabricator/branch to work on')


def _machine(parser):
    parser.add_argument('machine', help='machine on which the action will be performed')


def _repository(parser):
    parser.add_argument('repository', nargs='?', default='vyos-1x', help='the repository to work on')


def _router(parser):
    default = config.default.get('router', None)
    nargs = '?' if default else None
    parser.add_argument('router', nargs=nargs, default=default, help='router on which the packages will be installed')


def _server(parser):
    default = config.default.get('build', None)
    nargs = '?' if default else None
    parser.add_argument('server', nargs=nargs, default=default, help='server on which the action will be performed')


@register('target')
def _target(parser):
    parser.add_argument('target', help='target to create', default='./vyos')


# -- options

def _backdoor(parser):
    # to dangerous to have a -b option
    parser.add_argument('--backdoor', type=str, help='install an admin account on the iso with this passord')


def _bind(parser):
    parser.add_argument('-b', '--bind', type=int, metavar="IP", help='ip to bind the webserver to')


def _debug(parser):
    parser.add_argument('-d', '--debug', help='run python with pdb', action='store_true')


def _extra(parser):
    parser.add_argument('-e', '--extra', type=str, help='extra debian package(s) to install')


def _dry(parser):
    parser.add_argument('-d', '--dry', action='store_true', help='only show what will be done')


def _edit(parser):
    parser.add_argument('-e', '--edit', action='store_true', help='start editor once branched')


def _file(parser):
    parser.add_argument('-f', '--file', type=str, default='', help='iso file to save as')


def _iso(parser):
    parser.add_argument('-i', '--iso', type=str, default='', help='an vyos iso file to use')


def _quiet(parser):
    parser.add_argument('-q', '--quiet', action='store_true', help='do not show what is happening')


def _local(parser):
    parser.add_argument('-l', '--local', type=int, default=8088, metavar="PORT", help='port to bind the webserver')


def _packages(parser):
    parser.add_argument('-p', '--packages', type=str, nargs='*', default=['vyos-1x'], help='what vyos packages are considered')


def _name(parser):
    parser.add_argument('-n', '--name', type=str, help='name/tag to add to the build version')


def _release(parser):
    parser.add_argument('-r', '--release', type=str, help='make without custom package', choices=['current', 'crux'])


def _remote(parser):
    parser.add_argument('-r', '--remote', type=int,  metavar="PORT", help='ssh forward port to bind the router')


def _test(parser):
    parser.add_argument('-t', '--test', help='test the iso when built', action='store_true')


def _reboot(parser):
    # no short version for something so critical :p
    parser.add_argument('--reboot', action='store_true', help='reboot the router')


def _save(parser):
    parser.add_argument('-s', '--save', help='location where to save', action='store_true')


def _sudo(parser):
    parser.add_argument('--sudo', action='store_true', help='also setup sudo on this machine')


def _working(parser):
    parser.add_argument(
        '-w', '--working-dir', type=str, default='.', help='where the branch root is (where vyos repos where cloned)'
    )

# all programs are defined here


@register('edit')
def edit(parser):
    _edit(parser)
    _dry(parser)
    _quiet(parser)


@register('build')
def build(parser):
    _server(parser)
    _router(parser)
    # --
    _packages(parser)
    _working(parser)
    _dry(parser)
    _quiet(parser)


@register('branch')
def repository(parser):
    _branch(parser)
    _repository(parser)
    # --
    _edit(parser)
    _dry(parser)
    _quiet(parser)


@register('docker')
def docker(parser):
    _server(parser)
    # --
    _dry(parser)
    _quiet(parser)


@register('download')
def download(parser):
    _file(parser)
    _dry(parser)
    _quiet(parser)


@register('edit')
def edit(parser):
    _branch(parser)
    _repository(parser)
    # --
    _dry(parser)
    _quiet(parser)


@register('make')
def _make(parser):
    # --
    _extra(parser)
    _name(parser)
    _backdoor(parser)
    _release(parser)
    _test(parser)
    _save(parser)


@register('test')
def test(parser):
    _machine(parser)
    # --
    _dry(parser)
    _quiet(parser)


@register('update')
def release(parser):
    breakpoint()
    _router(parser)
    # --
    _packages(parser)
    _working(parser)
    _dry(parser)
    _quiet(parser)


@register('update')
def update(parser):
    _router(parser)
    # --
    _packages(parser)
    _working(parser)
    _dry(parser)
    _quiet(parser)


@register('upgrade')
def upgrade(parser):
    _router(parser)
    # --
    _bind(parser)
    _local(parser)
    _remote(parser)
    _iso(parser)
    _packages(parser)
    _working(parser)
    _file(parser)
    _reboot(parser)
    _dry(parser)
    _quiet(parser)


@register('release')
def release(parser):
    _target(parser)
    # --
    _debug(parser)
    _dry(parser)
    _quiet(parser)


@register('setup')
def mysetup(parser):
    _machine(parser)
    # --
    _sudo(parser)
    _dry(parser)
    _quiet(parser)


@register('ssh')
def ssh(parser):
    _machine(parser)
    # --
    _dry(parser)
    _quiet(parser)
