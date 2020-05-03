#!/usr/bin/env python3

import os
import re
import sys
import time
import datetime
import urllib.request

from vyosextra import arguments
from vyosextra.config import config


regex_rolling = '(vyos-1.3-rolling-[0-9]+-amd64.iso)'


def latest(filename):
	if filename:
		return filename.split('/')[-1]

	vyos_listing = "https://downloads.vyos.io/?dir=rolling/current/amd64"
	regex = re.compile(f'data-name="{regex_rolling}"')

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
		# should not happen, but something is better than nothing
		return 'vyos-rolling-latest.iso'


def makeup(target):
	if target.startswith('http'):
		image = target.split('/')[-1]
		location = os.path.join(config.get('global', 'store'), image)
	elif target.startswith('/'):
		image = target.split('/')[-1]
		location = target
	else:
		image = latest(target)
		location = os.path.join(config.get('global', 'store'), image)

	url = f'https://downloads.vyos.io/rolling/current/amd64/{image}'
	return image, location, url


def fetch(target='', show=False):
	image, location, url = makeup(target)

	if os.path.exists(location):
		print(f'already downloaded iso file {image}')
		return location

	print(f'downloading {url}')
	print(f'to          {location}')
	print('progress:')

	if show:
		return location

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
		report = f'   {image} {percent:>3}%, {progress_mb:3.2f} MB, {speed:>5} KB/s, {elapsed} seconds passed \r'
		sys.stdout.write(report)
		sys.stdout.flush()

	try:
		urllib.request.urlretrieve(url, location, hook)
		print('\ndownload complete')
		return location
	except KeyboardInterrupt:
		print('\ndownload interrupted')
		print(f'\nremoving {location}')
		os.remove(location)
		sys.exit(2)
	except Exception as excp:
		print(f'\nissue while downloading {image}')
		print(excp)
		print(f'\nremoving {location}')
		os.remove(location)
		sys.exit(3)


def main():
	'download latest VyOS rolling image'
	arg = arguments.setup(
		__doc__,
		['isofile', 'presentation']
	)
	code = fetch(arg.file)
	return code


if __name__ == '__main__':
	main()
