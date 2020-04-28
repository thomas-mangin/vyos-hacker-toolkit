#!/usr/bin/env python3

import os
import sys
import importlib
import setuptools

FOLDER = os.path.dirname(os.path.realpath(__file__))
IMPORT = os.path.abspath(os.path.join(FOLDER, 'lib','vyosextra','entry'))
if os.path.exists(IMPORT):
	sys.path.append(IMPORT)
else:
	sys.exit('could not determine the version')

VERSION = importlib.import_module('version').VERSION

ret = os.system(f'{FOLDER}/sbin/gendata --create')
if ret != 0:
	sys.exit('failed to generate data.py')

setuptools.setup(
	download_url='https://github.com/thomas-mangin/vyos-extra/archive/%s.tar.gz' % VERSION,
)

os.system(f'{FOLDER}/sbin/gendata --delete')
os.system(f'rm -rf {FOLDER}/build')
os.system(f'rm -rf {FOLDER}/lib/vyos_extra.egg-info')
