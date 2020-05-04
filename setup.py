#!/usr/bin/env python3

import os
import sys
import setuptools

here = os.path.dirname(os.path.realpath(__file__))
lib = os.path.abspath(os.path.join(here, 'lib'))

if not os.path.exists(lib):
    sys.exit(f'could not import "{lib}"')
sys.path.append(lib)

from vyosextra.entry.version import VERSION  # noqa: E402
from vyosextra.insource import generate  # noqa: E402
from vyosextra.insource import location  # noqa: E402

data = os.path.abspath(os.path.join(here, 'data'))
generate(data)
url = 'https://github.com/thomas-mangin/vyos-extra/archive/%s.tar.gz' % VERSION

setuptools.setup(
    download_url=url,
)

os.remove(location())

# cleanup
os.system(f'rm -rf {here}/build')
os.system(f'rm -rf {here}/lib/vyos_extra.egg-info')
