import os

from sqlalchemy import create_engine

from .base import Base, DBSession


def register_models(engine):
    Base.metadata.create_all(engine)


def unregister_models(engine):
    Base.metadata.reflect()
    Base.metata.drop_all(engine)


def configure_db(options, drop_all=False):

    sql_str = options["sqlalchemy.url"]
    timeout = options.get("sqlalchemy.timeout", None) or 600
    engine = create_engine(sql_str, pool_recycle=timeout)

    if drop_all or os.environ.get('BOOKIE_TEST_DB_STRING'):
        unregister_models(engine)

    #for populate in get_settings()['kotti.populators']:
    #    populate()
    #commit()

    register_models(engine)

    DBSession.registry.clear()
    DBSession.configure(bind=engine)
    Base.metadata.bind = engine


__all__ = ["register_models", "unregister_models", "configure_db", "models"]
