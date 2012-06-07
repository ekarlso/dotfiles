# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys
import datetime
import logging

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    relationship, backref, exc, object_mapper, synonym, validates,
        sessionmaker, scoped_session)
from sqlalchemy import (create_engine, Column, Integer, Unicode, BigInteger,
    Unicode, ForeignKey, Date, DateTime, Boolean, UnicodeText, UniqueConstraint, Table)
from zope.sqlalchemy import ZopeTransactionExtension


from ziggurat_foundations.models import BaseModel, UserMixin, GroupMixin, \
    GroupPermissionMixin, UserGroupMixin, GroupResourcePermissionMixin, \
    ResourceMixin, UserPermissionMixin, UserResourcePermissionMixin, \
    ExternalIdentityMixin
from ziggurat_foundations import ziggurat_model_init, models as zmodels


_ENGINE = None
_MAKER = None


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
zmodels.DBSession = DBSession


PERMISSIONS = ("add", "view", "edit", "delete", "retailer.admin",
                "system.admin")


class BaseModel(object):
    """
    Base class to make ones life working with models and python easier
    """
    __display_rows__ = None
    __display_string__ = None
    __table_args__ = {"mysql_engine": "InnoDB"}
    __table__initialized__ = False

    ROW_DISPLAY = None

    def save(self, session=None):
        session = session or get_session()
        session.add(self)
        session.flush()
        return self

    def delete(self, session=None):
        session.save(session=session)

    def update(self, values):
        for k, v in values.items():
            self[k] = v

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

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def keys(self):
        return self.__dict__.keys()

    def values(self):
        return self.__dict__.values()

    def items(self):
        local = dict(self)
        joined = dict([(k, v) for k, v in self.__dict__.items()
                     if not k[0] == "_"])
        local.update(joined)
        return local.items()

    def to_dict(self):
        return self.__dict__.copy()

    @property
    def display_rows(self):
        copy = self.to_dict()
        if not self.__display_rows__:
            return copy
        ret = {}
        for row_name in self.__display__rows__:
            ret[row_name] = copy[row_name]
        return ret

    def __unicode__(self):
        dn = self.__display_string__ or "name"
        if type(dn) == list:
            return self.display_string
        if not hasattr(self, dn):
            dn = "id"
        return getattr(self, dn)

    @property
    def display_string(self):
        copy = self.to_dict()
        display = ""
        if type(self.__display_string__) == list:
            display = []
            for i in self.__display_string__:
                 data = copy.get(i, None)
                 if data:
                    display.append(data)
            display = " ".join(display)
        else:
            display = self
        return unicode(display)


Base = declarative_base(cls=BaseModel)
Base.query = DBSession.query_property()


def register_models(engine):
    Base.metadata.create_all(engine)


def unregister_models(engine):
    Base.metata.drop_all(engine)


def configure_db(options):
    global _ENGINE
    global LOG
    if not _ENGINE:
        sql_str = options["sqlalchemy.url"]
        timeout = options.get("sqlalchemy.timeout", None) or 600
        _ENGINE = create_engine(sql_str, pool_recycle=timeout)

        LOG = logging.getLogger("sqlalchemy.engine")
        LOG.setLevel(logging.DEBUG)

        register_models(_ENGINE)

        DBSession.configure(bind=_ENGINE)
        Base.metadata.bind = _ENGINE


def get_session():
    """
    Get a session, currently just gives DBSession
    """
    return DBSession


class Group(Base, GroupMixin):
    """
    An organisation - typically something with users and customers
    """
    __possible_permissions__ = PERMISSIONS
    organisation_id = Column(Integer)
    customers = relationship("Customer", backref="retailer")


class GroupPermission(Base, GroupPermissionMixin):
    """
    Give a Group a Permission
    """
    pass


class GroupResourcePermission(Base, GroupResourcePermissionMixin):
    """
    Gives a Group Permission to a Resource
    """
    pass


class Resource(Base, ResourceMixin):
    pass


class UserGroup(Base, UserGroupMixin):
    """
    Map a User to a Group
    """
    pass


class User(Base, UserMixin):
    __display_string__ = ["first_name", "middle_name", "last_name"]
    __possible_permissions__ = PERMISSIONS
    first_name = Column(UnicodeText)
    middle_name = Column(UnicodeText)
    last_name = Column(UnicodeText)
    name = Base.display_string


class UserPermission(Base, UserPermissionMixin):
    """
    A user permission
    """
    pass


class UserResourcePermission(Base, UserResourcePermissionMixin):
    """
    Give a User Permission to a Resource
    """
    pass


class ExternalIdentity(Base, ExternalIdentityMixin):
    pass


class Customer(Base):
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    organisation_id = Column(Integer)
    contact = Column(UnicodeText)
    email = Column(UnicodeText)
    phone = Column(Integer)
    retailer_id = Column(Integer, ForeignKey('groups.id'))


# NOTE: Map categories >< entities
category_entity_map = Table('category_entity_map', Base.metadata,
    Column('category_id', Integer, ForeignKey('category.id')),
    Column('entity_id', Integer, ForeignKey('entity.id'))
)


# NOTE: Map categories >< categories
category_map = Table('category_map', Base.metadata,
    Column("parent_id", Integer, ForeignKey("category.id"), primary_key=True),
    Column("child_id", Integer, ForeignKey("category.id"), primary_key=True)
)


class Category(Base):
    """
    A entity category is owned by a retailer
    """
    __tablename__ = "category"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), nullable=False)
    description = Column(UnicodeText)

    resource_id = Column(Integer, ForeignKey("resources.resource_id"))
    resources = relationship("Resource", backref="categories")

    categories = relationship("Category", secondary=category_map,
                            primaryjoin=id==category_map.c.parent_id,
                            secondaryjoin=id==category_map.c.child_id,
                            backref="parent_categories")
    entities = relationship("Entity", secondary=category_entity_map,
                            backref="categories")


category_meta_table = Table('category_meta_map', Base.metadata,
    Column('category_id', Integer, ForeignKey('category.id')),
    Column('meta_id', Integer, ForeignKey('category_meta.id'))
)


class CategoryMeta(Base):
    __tablename__ = "category_meta"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255))
    value = Column(UnicodeText, nullable=True)


class Entity(Base):
    """
    A Entity is a product / thing to be rented out to a customer
    """
    __tablename__ = "entity"
    id = Column(Integer, primary_key=True)
    brand = Column(UnicodeText)
    model = Column(UnicodeText)
    identifier = Column(UnicodeText, unique=True)
    produced = Column(Integer)

    def __unicode__(self):
        return "%s %s (%d)" % (self.brand, self.model, self.produced)


class Property(Base):
    __tablename__ = "entity_property"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(255), index=True, nullable=False)
    value = Column(UnicodeText, nullable=True)
    entity_id = Column(Integer, ForeignKey("entity.id"))
    entity = relationship("Entity", backref="properties")


class DrivableEntity(Entity):
    """
    Represent a drivable entity
    """
    @property
    def gps(self, value=None):
        print "gps" in self.properties


Car = DrivableEntity


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)

    start_date = Column(Date, default=datetime.datetime.now())
    start_time = Column(Unicode)
    start_location = Column(UnicodeText)

    end_date = Column(Date, default=datetime.datetime.now())
    end_time = Column(Unicode)
    end_location = Column(UnicodeText)

    price = Column(Integer)

    customer_id = Column(Integer, ForeignKey('customer.id'))
    customer = relationship("Customer", backref="orders")

    entity_id = Column(Integer, ForeignKey('entity.id'))
    entity = relationship("Entity", backref="orders")


ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                    UserResourcePermission, GroupResourcePermission, Resource,
                    ExternalIdentity)
