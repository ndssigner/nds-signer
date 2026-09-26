# NDS-Signer - `importlib.import_module` for MicroPython.
import sys


def import_module(name, package=None):
    __import__(name)
    return sys.modules[name]
