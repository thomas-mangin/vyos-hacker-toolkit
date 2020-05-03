#!/usr/bin/env python3

import sys
import pkgutil
import importlib

from vyosextra.register import Registerer


def import_all(package_name):
    package = sys.modules[package_name]
    return {
        name: importlib.import_module(package_name + '.' + name)
        for loader, name, is_pkg in pkgutil.walk_packages(package.__path__)
    }

__modules = import_all(__name__)
__all__ = __modules.keys()


# register the entry points in the module

register = Registerer()
for name, module in __modules.items():
	register(name,module.main)
