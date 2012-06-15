from datetime import datetime
import logging
import pdb

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
    __expose_attrs__ = None
    __title_attrs__ = None
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
        self.deleted = True
        self.deleted_at = datetime.utcnow()
        self.save(session=session)

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

    def values(self, attrs=None):
        attrs = attrs or self.keys()
        return [self.__dict__[k] for k in keys]

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

    @classmethod
    def exposed_attrs(cls, attrs=None):
        """
        Returns the either given or attrs set in __exposed_attrs__
        """
        attrs = attrs or cls.__expose_attrs__
        if not attrs and isinstance(cls, BaseModel):
            attrs = attrs.keys()
        return attrs

    def format_self(self, format_string=None):
        """
        Return a list of expose values
        """
        format = format_string or self.__format_string__
        return format.format(**self)

    @property
    def title(self):
        return self.format_self()

    def __unicode__(self):
        return self.format_self()


Base = declarative_base(cls=BaseModel)
Base.query = DBSession.query_property()
