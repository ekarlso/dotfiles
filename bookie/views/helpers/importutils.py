# vim: tabstop=4 shiftwidth=4 softtabstop=4

"""
Import related utilities and helper functions.
"""

import sys


def import_class(import_str):
    """Returns a class from a string including module and class"""
    mod_str, _sep, class_str = import_str.rpartition('.')
    try:
        __import__(mod_str)
        return getattr(sys.modules[mod_str], class_str)
    except (ImportError, ValueError, AttributeError), exc:
        raise ImportError('Class %s cannot be found (%s)' %
                (class_str, str(exc)))


def import_object(import_str, *args, **kwargs):
    """Import a class and return an instance of it."""
    return import_class(import_str)(*args, **kwargs)


def import_module(import_str):
    """Import a module."""
    __import__(import_str)
    return sys.modules[import_str]
