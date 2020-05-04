#!/usr/bin/env python3

import os
import sys
import importlib
import setuptools

here = os.path.dirname(os.path.realpath(__file__))
lib = os.path.abspath(os.path.join(here, 'lib'))

if not os.path.exists(lib):
	sys.exit(f'could not import "{lib}"')
sys.path.append(lib)

from vyosextra.entry.version import VERSION
from vyosextra.insource import generate
from vyosextra.insource import location

data = os.path.abspath(os.path.join(here, 'data'))
generate(data)

setuptools.setup(
	download_url='https://github.com/thomas-mangin/vyos-extra/archive/%s.tar.gz' % VERSION,
)

os.remove(location())

# cleanup
os.system(f'rm -rf {here}/build')
os.system(f'rm -rf {here}/lib/vyos_extra.egg-info')
