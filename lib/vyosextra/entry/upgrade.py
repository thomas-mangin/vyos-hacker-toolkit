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

from vyosextra.entry.download import makeup
from vyosextra.entry.download import fetch


class Command(cmd.Command):
	def upgrade(self, where, url):
		# on my local VM which goes to sleep when I close my laptop
		# time can easily get out of sync, which prevent apt to work
		now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		self.ssh(where, f"sudo date -s '{now}'")
		self.ssh(where, f"printf 'yes\n\nyes\nyes\nyes\n' | sudo /opt/vyatta/sbin/install-image {url}")
		self.ssh(where, 'printf 1 | /opt/vyatta/bin/vyatta-boot-image.pl --select')
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

def web(name, location, port):
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

	parser.add_argument('-i', '--ip', type=str, help="ip to bind the webserver")
	parser.add_argument('-p', '--port', type=int, help="port to bind the webserver", default=8888)

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

	ip = args.ip if args.ip else socket.gethostbyname(socket.gethostname())
	port = args.port
	name, location, url = makeup('')

	fetch()

	if not args.show:
		print(f'serving on: http://{ip}:{port}/{name}')
		web(name, location, port)

	time.sleep(0.1)
	cmds.upgrade(args.router, f'http://{ip}:{port}/{name}')

if __name__ == '__main__':
	upgrade()
