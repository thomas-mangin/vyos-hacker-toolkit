#!/usr/bin/env python3

import os
import sys
import time
import socket
import shutil
from datetime import datetime

from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler

from vyosextra import control
from vyosextra import arguments

from vyosextra.config import config
from vyosextra.entry.download import fetch


class Control(control.Control):
	def upgrade(self, where, ip, location, local, remote, show):
		# local: your computer port
		# remote: the router port
		image = location.split('/')[-1]

		if local and remote:
			url = f'http://127.0.0.1:{remote}/{image}'
			extra = f'-R {remote}:127.0.0.1:{local}'
		else:
			ip = ip if ip else socket.gethostbyname(socket.gethostname())
			url = f'http://{ip}:{local}/{image}'
			extra = ''

		print(f'serving on: {url}')
		print(f'from image: {location}')
		if not show:
			web(location, image, local)

		self.ssh(where, f"printf 'yes\n\nyes\nyes\nyes\n' | sudo /opt/vyatta/sbin/install-image {url}", extra=extra)
		self.ssh(where, 'printf 1 | /opt/vyatta/bin/vyatta-boot-image.pl --select')

	def reboot(self, where):
		# should find a way to check if the image changed
		self.ssh(where, 'sudo reboot')


def start_server(path, file, port):
	class Handler(SimpleHTTPRequestHandler):
		def do_GET(self):
			if self.path != f'/{file}':
				return

			with open(os.path.join(path, file), 'rb') as f:
				fs = os.fstat(f.fileno())

				self.send_response(200)
				self.send_header("Content-type", "application/octet-stream")
				self.send_header("Content-Disposition", f'attachment; filename="{file}"')
				self.send_header("Content-Length", str(fs.st_size))
				self.end_headers()

				shutil.copyfileobj(f, self.wfile)

	os.chdir(path)
	httpd = HTTPServer(('', port), Handler)
	httpd.serve_forever()
	sys.exit(1)


def web(location, name, port):
	daemon = Thread(
		name='serve VyOS',
		target=start_server,
		args=(os.path.dirname(location), name, port)
	)

	daemon.setDaemon(True)
	daemon.start()


def main():
	'upgrade router to latest VyOS image'
	arg = arguments.setup(
		__doc__,
		['router', 'upgrade', 'presentation']
	)
	control = Control(arg.show, arg.verbose)

	if not config.exists(arg.router):
		sys.stderr.write(f'machine "{arg.router}" is not configured\n')
		sys.exit(1)

	role = config.get(arg.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{arg.router}" is not a VyOS router\n')
		sys.exit(1)

	location = fetch(arg.file)

	if arg.remote and not arg.local:
		local = arg.remote
		remote = arg.remote
	else:
		local = arg.local
		remote = arg.remote

	time.sleep(0.1)
	control.upgrade(arg.router, arg.bind, location, local, remote, arg.show)
	if arg.reboot:
		control.reboot(arg.router)


if __name__ == '__main__':
	main()
