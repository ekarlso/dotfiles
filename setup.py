import codecs
import os
import sys

from distutils.util import convert_path
from fnmatch import fnmatchcase
from setuptools import setup, find_packages

import setup_utils


def read(fname):
    return codecs.open(os.path.join(os.path.dirname(__file__), fname)).read()


requires = setup_utils.parse_requirements()
dependency_links = setup_utils.parse_dependency_links()
tests_require = setup_utils.parse_requirements(['tools/test-requires'])


# Provided as an attribute, so you can append to these instead
# of replicating them:
standard_exclude = ["*.py", "*.pyc", "*$py.class", "*~", ".*", "*.bak"]
standard_exclude_directories = [
    ".*", "CVS", "_darcs", "./build", "./dist", "EGG-INFO", "*.egg-info"
]


# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
# Note: you may want to copy this into your setup.py file verbatim, as
# you can't import this from another package, when you don't know if
# that package is installed yet.
def find_package_data(
    where=".",
    package="",
    exclude=standard_exclude,
    exclude_directories=standard_exclude_directories,
    only_in_packages=True,
    show_ignored=False):
    """
    Return a dictionary suitable for use in ``package_data``
    in a distutils ``setup.py`` file.

    The dictionary looks like::

        {"package": [files]}

    Where ``files`` is a list of all the files in that package that
    don"t match anything in ``exclude``.

    If ``only_in_packages`` is true, then top-level directories that
    are not packages won"t be included (but directories under packages
    will).

    Directories matching any pattern in ``exclude_directories`` will
    be ignored; by default directories with leading ``.``, ``CVS``,
    and ``_darcs`` will be ignored.

    If ``show_ignored`` is true, then all the files that aren"t
    included in package data are shown on stderr (for debugging
    purposes).

    Note patterns use wildcards, or can be exact paths (including
    leading ``./``), and all searching is case-insensitive.
    """
    out = {}
    stack = [(convert_path(where), "", package, only_in_packages)]
    while stack:
        where, prefix, package, only_in_packages = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "Directory %s ignored by pattern %s"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                if (os.path.isfile(os.path.join(fn, "__init__.py"))
                    and not prefix):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + "." + name
                    stack.append((fn, "", new_package, False))
                else:
                    stack.append((fn, prefix + name + "/", package, only_in_packages))
            elif package or not only_in_packages:
                # is a file
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        if show_ignored:
                            print >> sys.stderr, (
                                "File %s ignored by pattern %s"
                                % (fn, pattern))
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out


PACKAGE = "bookie"
NAME = "BookieFrontend"
DESCRIPTION = "Frontend for bookie"
AUTHOR = "Endre Karlson"
AUTHOR_EMAIL = "endre.karlson@gmail.com"
URL = ""
#VERSION = __import__(PACKAGE).__version__
VERSION = "0.1"

setup(name='bookie',
      version = VERSION,
      description=DESCRIPTION,
      long_description=read("README.md"),
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pylons",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(exclude=["tests.*", "tests"]),
      package_data=find_package_data(PACKAGE, only_in_packages=False),
      include_package_data=True,
      message_extractors  = { ".": [
        ('**/docs/**', 'ignore', None),
        ('**/static/**', 'ignore', None),
        ('**.py',   'lingua_python', None ),
        ('**.pt',   'lingua_xml', None ),
        ('**.html',   'mako', None ),
        ('**.mako',   'mako', None ),
      ]},
      zip_safe=False,
      cmdclass=setup_utils.get_cmdclass(),
      dependency_links=dependency_links,
      tests_require=tests_require,
      setup_requires=['setuptools-git>=0.4', "setuptools-hg"],
      test_suite="nose.collector",
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = bookie:main
      [console_scripts]
      initialize_bookie_db = bookie.scripts.initializedb:main
      bookie-db-shell = bookie.scripts.db_shell:main
      """
      )

