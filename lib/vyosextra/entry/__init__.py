#!/usr/bin/env python3

from os.path import join
from os.path import abspath
from os.path import dirname
from os.path import basename
from glob import glob
from importlib import import_module

dispatch = {}

for fname in glob(join(abspath(dirname(__file__)),'[a-z]*.py')):
	name = basename(fname).split('.')[0]
	module = import_module(f'vyosextra.entry.{name}')
	function = getattr(module, 'main')
	documentation = function.__doc__
	locals()[name] = module
	dispatch[name] = (function, documentation)
