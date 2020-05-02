#!/usr/bin/env python3

import os
import sys
import time
import socket
import shutil
import argparse
from datetime import datetime

from threading import Thread
from http.server import HTTPServer, SimpleHTTPRequestHandler

from vyosextra import cmd
from vyosextra.config import Config

from vyosextra.entry.download import fetch


class Command(cmd.Command):
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

def upgrade():
	parser = argparse.ArgumentParser(description='upgrade router to latest VyOS image')
	parser.add_argument('router', help='machine on which the action will be performed')

	parser.add_argument('-f', '--file', type=str, default='', help='iso file to save as')
	parser.add_argument('-b', '--bind', type=int, help="ip to bind the webserver to")
	parser.add_argument('-r', '--remote', type=int, help="port to bind the router")
	parser.add_argument('-l', '--local', type=int, help="port to bind the webserver", default=8088)
	# no short version for something so critical :p
	parser.add_argument('--reboot', help='reboot the router', action='store_true')

	parser.add_argument('-s', '--show', help='only show what will be done', action='store_true')
	parser.add_argument('-v', '--verbose', help='show what is happening', action='store_true')
	parser.add_argument('-d', '--debug', help='provide debug information', action='store_true')

	args = parser.parse_args()

	cmds = Command(args.show, args.verbose)

	if not cmds.config.exists(args.router):
		sys.stderr.write(f'machine "{args.router}" is not configured\n')
		sys.exit(1)

	role = cmds.config.get(args.router, 'role')
	if role != 'router':
		sys.stderr.write(f'target "{args.router}" is not a VyOS router\n')
		sys.exit(1)

	location = fetch(args.file)

	if args.remote and not args.local:
		local = args.remote
		remote = args.remote
	else:
		local = args.local
		remote = args.remote

	time.sleep(0.1)
	cmds.upgrade(args.router, args.bind, location, local, remote, args.show)
	if args.reboot:
		cmds.reboot(args.router)

if __name__ == '__main__':
	upgrade()
