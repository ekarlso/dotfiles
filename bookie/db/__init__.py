import os
from pprint import pformat

from pyramid.threadlocal import get_current_registry
from sqlalchemy import create_engine

#from .. import get_settings
import bookie
from .base import Base, DBSession


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

    DBSession.registry.clear()
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine

    if drop_all or os.environ.get('BOOKIE_TEST_DB_STRING'):
        unregister_models(engine)

    register_models(engine)

    for populate in settings['bookie.populators']:
        populate()
    return engine

__all__ = ["register_models", "unregister_models", "configure_db", "models",
        "DBSession"]
