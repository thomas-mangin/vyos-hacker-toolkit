import re
import argparse

from vyosextra.register import Registerer
register = Registerer()


def setup(description, options, strict=True):
	parser = argparse.ArgumentParser(description=description)
	for option in options:
		register.call(option,parser)

	# oops, another pdb built-in name :p
	args = [parser.parse_args()] if strict else parser.parse_known_args()

	if 'repository' in options:
		_query_valid_vyos(args[0].branch, args[0].repository)
	return args[0]


def _query_valid_vyos(branch, repository):
	if not re.match('T[0-9]+', branch):
		input('your branch name does not look like a phabricator entry (like T2000)')

	if repository is None:
		repository = '.'
	elif not repository.startswith('vyos-') and not repository.startswith('vyatta-'):
		input('your repository name does not look like a vyos project (like vyos-1x)')


@register('target')
def _target(parser):
	parser.add_argument("target", help='make target')


@register('machine')
def _machine(parser):
	parser.add_argument("machine", help='machine on which the action will be performed')


@register('router')
def _router(parser):
	parser.add_argument('router', help='router on which the packages will be installed')


@register('server')
def _server(parser):
	parser.add_argument("server", help='server on which the action will be performed')


@register('package')
def _package(parser):
	parser.add_argument(
		'-p', '--packages', type=str, nargs='*',
		choices=['vyos-1x', 'vyatta-op', 'vyatta-cfg', 'smoketest'],
		default='vyos-1x',
		help='what type of package is it')
	parser.add_argument(
		'-l', '--location', type=str,
		default='..',
		help='where the repository is')


@register('make')
def _make(parser):
	parser.add_argument('-e', '--extra', type=str, help='extra debian package(s) to install')
	parser.add_argument('-n', '--name', type=str, help='name/tag to add to the build version')
	parser.add_argument('-b', '--backdoor', type=str, help='install an admin account on the iso with this passord')
	parser.add_argument('-f', '--force', help="make without custom package", action='store_true')
	parser.add_argument('-t', '--test', help='test the iso when built', action='store_true')


@register('repository')
def _repository(parser):
	parser.add_argument("branch", help='the phabricator/branch to work on')
	parser.add_argument("repository", help='the repository to work on')


@register('presentation')
def _presentation(parser):
	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')


@register('isofile')
def _isofile(parser):
	parser.add_argument('-f', '--file', type=str, default='', help='iso file to save as')


@register('edit')
def _edit(parser):
	parser.add_argument('-e', '--edit', help='start editor once branched', action='store_true')


@register('upgrade')
def _upgrade(parser):
	parser.add_argument('router', help='machine on which the action will be performed')
	parser.add_argument('-f', '--file', type=str, default='', help='iso file to save as')
	parser.add_argument('-b', '--bind', type=int, help="ip to bind the webserver to")
	parser.add_argument('-r', '--remote', type=int, help="port to bind the router")
	parser.add_argument('-l', '--local', type=int, help="port to bind the webserver", default=8088)
	# no short version for something so critical :p
	parser.add_argument('--reboot', help='reboot the router', action='store_true')
