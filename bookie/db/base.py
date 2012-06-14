from datetime import datetime
import logging

from colanderalchemy import SQLAlchemyMapping
from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import object_mapper, scoped_session, sessionmaker
from zope.sqlalchemy import ZopeTransactionExtension


LOG = logging.getLogger(__name__)


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def get_session():
    return DBSession


class BaseModel(object):
    """
    Base class to make ones life working with models and python easier
    """
    __display_columns__ = None
    __display_string__ = None
    __hide_attrs__ = None
    __table_args__ = {"mysql_engine": "InnoDB"}
    __table__initialized__ = False
    __protected_attributes__ = set([
        "created_at", "updated_at", "deleted_at", "deleted"])

    created_at = Column(DateTime, default=datetime.utcnow,
        nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow(),
        nullable=False, onupdate=datetime.utcnow())
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, nullable=False, default=False)

    def save(self, session=None):
        session = session or get_session()
        session.add(self)
        session.flush()
        return self

    def delete(self, session=None):
        session.save(session=session)

    def update(self, values):
        for k, v in values.items():
            LOG.debug("Key %s - %s" % (k, v))
            self[k] = v
        return self

    def __contains__(self, key):
        if hasattr(self, key):
            return True
        else:
            return False

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return getattr(self, key)

    def __iter__(self):
        self._i = iter(object_mapper(self).columns)
        return self

    @property
    def hide_attrs(self):
        """Protected attributes - shouldn't be exposed"""
        protected = self.__hide_attrs__ or []
        protected.append("_sa_instance_state")
        return protected

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def keys(self):
        return [k for k in self.__dict__.keys() \
            if k not in self.hide_attrs]

    def values(self):
        return [self.__dict__[k] for k in self.keys()]

    def items(self):
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.items()
                     if not k[0] == "_"])
        local.update(joined)
        return local.items()

    def to_dict(self):
        return self.__dict__.copy()

    @classmethod
    def get_schema(cls):
        return SQLAlchemyMapping(cls)

    @property
    def display_columns(self):
        copy = self.to_dict()
        if not self.__display_columns__:
            return copy
        ret = {}
        for row_name in self.__display_columns__:
            ret[row_name] = copy[row_name]
        return ret

    def __unicode__(self):
        dn = self.__display_string__ or "name"
        if type(dn) == list:
            return self.display_string
        if not hasattr(self, dn):
            dn = "id"
        return getattr(self, dn)

    @classmethod
    def exposed_columns(cls):
        return cls.__display_columns__

    @property
    def display_string(self):
        copy = self.to_dict()
        display = ""
        if type(self.__display_string__) == list:
            display = []
            for i in self.__display_string__:
                 data = copy.get(i, None)
                 if data:
                    display.append(unicode(data))
            display = " ".join(display)
        else:
            display = self
        return unicode(display)

    title = display_string


Base = declarative_base(cls=BaseModel)
Base.query = DBSession.query_property()
