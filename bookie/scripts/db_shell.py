"""
The SQLAlchemy Shell.

This is just a wrapper for code.InteractiveConsole with some useful
defaults for using SQLAlchemy
"""

import os
import sys
from code import InteractiveConsole
from pyramid.paster import get_appsettings, setup_logging
import readline
import atexit

from ..models import configure_db, get_session, models as m


def detect_root_dir():
    """Detects the directory of the 'current' project for bootstrap
    purposes."""
    root_dir = None
    if root_dir is None:
        dircur = os.getcwd()
        last_dir = None
        while dircur != last_dir:
            for marker_file in ("setup.py", ".sqlalchemy"):
                if os.path.exists(os.path.join(dircur, marker_file)):
                    root_dir = dircur
                    break
            if root_dir is not None:
                break
            last_dir = dircur
            dircur = os.path.dirname(dircur)
    if not root_dir:
        raise Exception(
            "Unable to locate project root_dir: pass as 1st parameter"
        )
    return root_dir


def _banner(symbols):
    """Shows the currently defined symbols for use by the interactive shell.
    must be passed in the currently active symbol table, as a dictionary."""
    import os
    (_height, _width) = os.popen('stty size', 'r').read().split()
    _width = int(_width)
    print "Welcome to the SQLAlchemy shell.  This is a python shell, with "
    print "these globals defined:"
    count = 0
    for (_x, _v) in symbols.items():
        if not _x.startswith("_"):
            count += 1
            r = repr(_v)
            if (len(_x) + len(r) + len(" = ") + 1) > _width:
                r = r[0:(_width - len(_x) - 4 - 4)] + "..."
            print "  \033[1m{x}\033[0m = {v}".format(x=_x, v=r)


class SQLAlchemyShell(InteractiveConsole):
    """A subclass of the code.InteractiveConsole class, adding a history file
    and readline support.

    Mac OS X Lion users may need to:

        sudo easy_install readline

    To get a readline library which isn't b0rked."""

    def __init__(self, locals=None, filename="<console>", histfile=None):
        if histfile is None:
            histfile = os.path.expanduser("~/.sqlalchemy-shell-history")
        InteractiveConsole.__init__(self, locals, filename)
        self.init_history(histfile)
        self.init_completer()

    def init_completer(self):
        import rlcompleter
        self.completer = rlcompleter.Completer(namespace=self.locals)
        readline.set_completer(self.completer.complete)
        if 'libedit' in readline.__doc__:
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

    def init_history(self, histfile):
        if hasattr(readline, "read_history_file"):
            try:
                readline.read_history_file(histfile)
            except IOError:
                pass
            atexit.register(self.save_history, histfile)

    def save_history(self, histfile):
        readline.write_history_file(histfile)


def main(argv=sys.argv):
    root_dir = None
    if len(argv) > 1:
        root_dir = argv[1]
    else:
        root_dir = detect_root_dir()

    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)

    if os.environ.get("BOOKIE_DB_STR"):
        settings["sqlalchemy.url"] = os.environ.get("BOOKIE_DB_STR")

    # NOTE: This takes care of creating tables but not alembic
    engine = configure_db(settings)


    ic = SQLAlchemyShell()

    cmd = "from bookie.models.models import *"
    print ">>>", cmd
    ic.push(cmd)

    ic.push("from bookie.scripts.db_shell import _banner")
    ic.push("_banner(globals())")

    ic.interact(banner="Use quit() or Ctrl-D (i.e. EOF) to exit")
