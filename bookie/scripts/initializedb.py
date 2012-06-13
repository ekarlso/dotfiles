import os
import sys
from pprint import pformat
from random import choice
import transaction

from pyramid.paster import get_appsettings, setup_logging

from ..db import configure_db


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    settings["bookie.populators"] = "bookie.populate.populate_samples"

    configure_db(settings)
