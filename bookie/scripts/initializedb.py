import os
import sys
from pprint import pformat
from random import choice
import transaction

from alembic.config import Config
from alembic import command
from pyramid.paster import get_appsettings, setup_logging

from ..models import configure_db


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

    drop_all = True if os.environ.get("BOOKIE_DB_RELOAD") else False
    if os.environ.get("BOOKIE_DB_STR"):
        settings["sqlalchemy.url"] = os.environ.get("BOOKIE_DB_STR")

    # NOTE: This takes care of creating tables but not alembic
    configure_db(settings, drop_all=drop_all)

    alembic_cfg = Config("alembic_ziggurat.ini")
    command.stamp(alembic_cfg, "head")
    alembic_cfg = Config("alembic.ini")
    command.stamp(alembic_cfg, "head")
