import os
import re
from pprint import pformat

from pyramid.threadlocal import get_current_registry
from sqlalchemy import create_engine, event

#from .. import get_settings
import bookie
from .base import *
from .models import *


def register_models(engine):
    Base.metadata.create_all(engine)


def unregister_models(engine):
    Base.metadata.reflect()
    Base.metadata.drop_all(engine)


def configure_db(settings=None, drop_all=False):
    if settings:
        if not "bookie.populators" in settings:
            settings["bookie.populators"] = \
                bookie.CONF_DEFAULTS["bookie.populators"]
        bookie._resolve_dotted(settings, keys=["bookie.populators"])
    else:
        settings = bookie.get_settings()

    sql_str = settings["sqlalchemy.url"]
    timeout = settings.get("sqlalchemy.timeout", None) or 600
    engine = create_engine(sql_str, pool_recycle=timeout)

    # NOTE: Enable FK Pragma for sqlite.
    def _fk_pragma_on_connect(dbapi_con, con_record):
        dbapi_con.execute('pragma foreign_keys=ON')
    if re.search("^sqlite:", sql_str):
        event.listen(engine, 'connect', _fk_pragma_on_connect)

    DBSession.registry.clear()
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    if drop_all:
        unregister_models(engine)

    register_models(engine)

    for populate in settings['bookie.populators']:
        populate()
    return engine

__all__ = ["register_models", "unregister_models", "configure_db", "models",
        "DBSession"]
