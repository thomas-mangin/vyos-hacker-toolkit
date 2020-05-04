from vyosextra.config import config
from vyosextra import command

class Control(object):
	move = [
				('python/vyos/*', '/usr/lib/python3/dist-packages/vyos/'),
				('src/conf_mode/*', '/usr/libexec/vyos/conf_mode/'),
				('src/op_mode/*', '/usr/libexec/vyos/op_mode/'),
			]

	def __init__(self, dry, quiet):
		self.dry = dry
		self.verbose = not quiet

	def run(self, cmd, **kargs):
		return command.run(cmd, self.dry, self.verbose, **kargs)

	def chain(self, cmd1, cmd2, **kargs):
		return command.chain(cmd1, cmd2, self.dry, self.verbose, **kargs)

	def ssh(self, where, cmd, ignore='', extra='', hide='', exitonfail=True, quote=True):
		return command.run(
			config.ssh(where, cmd, extra=extra, quote=quote),
			self.dry, self.verbose,
			ignore=ignore, hide=hide, exitonfail=exitonfail
		)

	def scp(self, where, src, dst):
		return command.run(
			config.scp(where, src, dst), 
			self.dry, self.verbose
		)
