#!/usr/bin/env python3

import os
import sys
import time
import argparse
import datetime
import urllib.request


vyos_url = 'https://downloads.vyos.io/rolling/current/amd64/vyos-rolling-latest.iso'
filename = 'vyos-rolling-latest.iso'

# modified from:
# https://blog.shichao.io/2012/10/04/progress_speed_indicator_for_urlretrieve_in_python.html

def download(url=vyos_url, filename=filename):
	parser = argparse.ArgumentParser(description='download latest VyOS image')
	parser.add_argument('-f', '--file', type=str, default=filename, help='iso file to save as')
	args = parser.parse_args()

	location = args.file
	filename = os.path.basename(location)

	start_time = time.time()

	def hook(count, block_size, total_size):
		duration = time.time() - start_time
		elapsed = str(datetime.timedelta(seconds=duration)).split('.')[0]
		progress = int(count * block_size)
		speed = int(progress / (1024 * (int(duration) + 1)))
		percent = min(int(count*block_size*100/total_size), 100)
		progress_mb = progress / (1024 * 1024)
		report = f'  {filename} {percent:>3}%, {progress_mb:3.2f} MB, {speed:>5} KB/s, {elapsed} seconds passed \r'
		sys.stdout.write(report)
		sys.stdout.flush()

	try:
		urllib.request.urlretrieve(url, location, hook)
		print('\ndownload complete')
	except KeyboardInterrupt:
		print(f'\nremoving {location}')
		os.remove(location)


if __name__ == '__main__':
	download()
