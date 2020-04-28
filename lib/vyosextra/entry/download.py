#!/usr/bin/env python3

import os
import re
import sys
import time
import argparse
import datetime
import urllib.request


vyos_rolling = '(vyos-1.3-rolling-[0-9]+-amd64.iso)'


def latest():
	vyos_listing = "https://downloads.vyos.io/?dir=rolling/current/amd64"
	regex = re.compile(f'data-name="{vyos_rolling}"')

	try:
		opener = urllib.request.FancyURLopener({})
		with opener.open(vyos_listing) as f:
			content = f.read().decode('utf-8')

		found = regex.findall(content)
		if not found:
			return ''
		found.sort()
		return found[-1]
	except Exception:
		return ''


def makeup(filename):
	name = ''
	location = ''

	if filename:
		base = filename.split('/')[-1]
		if re.match(vyos_rolling, base):
			if not filename.startswith('https://'):
				location = filename
			name = base

	if not name:
		try:
			name = latest()
		except KeyboardInterrupt:
			sys.exit(2)
		except Exception:
			# should not happen, but something is better than nothing
			name = 'vyos-rolling-latest.iso'

	if not location:
		location = name

	url = f'https://downloads.vyos.io/rolling/current/amd64/{name}'

	return (name, os.path.abspath(location), url)


def download():
	parser = argparse.ArgumentParser(description='download latest VyOS image')
	parser.add_argument('-f', '--file', type=str, default='', help='iso file to save as')
	args = parser.parse_args()

	name, location, url = makeup(args.file)
	print(f'downloading {url}')
	print(f'to          {location}')

	if os.path.exists(location):
		print(f'already downloaded iso file {name}')
		sys.exit(1)

	# modified from:
	# https://blog.shichao.io/2012/10/04/progress_speed_indicator_for_urlretrieve_in_python.html

	start_time = time.time()

	def hook(count, block_size, total_size):
		duration = time.time() - start_time
		elapsed = str(datetime.timedelta(seconds=duration)).split('.')[0]
		progress = int(count * block_size)
		speed = int(progress / (1024 * (int(duration) + 1)))
		percent = min(int(count*block_size*100/total_size), 100)
		progress_mb = progress / (1024 * 1024)
		report = f'  {name} {percent:>3}%, {progress_mb:3.2f} MB, {speed:>5} KB/s, {elapsed} seconds passed \r'
		sys.stdout.write(report)
		sys.stdout.flush()

	try:
		urllib.request.urlretrieve(url, location, hook)
		print('\ndownload complete')
	except KeyboardInterrupt:
		print(f'\nremoving {location}')
		os.remove(location)
		sys.exit(2)
	except Exception:
		print(f'\nremoving {location}')
		os.remove(location)
		sys.exit(3)


if __name__ == '__main__':
	download()
