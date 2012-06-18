# vim: tabstop=4 shiftwidth=4 softtabstop=4

import sys
import datetime
import logging
from pprint import pformat
from UserDict import UserDict

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, backref, exc, object_mapper, \
    synonym, validates
from sqlalchemy import Column, Integer, Unicode, BigInteger, \
    Unicode, ForeignKey, Date, DateTime, Boolean, UnicodeText, UniqueConstraint, Table

from ziggurat_foundations.models import BaseModel, UserMixin, GroupMixin, \
    GroupPermissionMixin, UserGroupMixin, GroupResourcePermissionMixin, \
    ResourceMixin, UserPermissionMixin, UserResourcePermissionMixin, \
    ExternalIdentityMixin
from ziggurat_foundations import ziggurat_model_init, models as zm

from ..utils import camel_to_name, name_to_camel
from .base import Base, DBSession


LOG = logging.getLogger(__name__)

zm.DBSession = DBSession


PERMISSIONS = {
    "add": {"title": "Add"},
    "view": {"title": "View"},
    "edit": {"title": "Edit"},
    "delete": {"title": "Delete"},
    "retailer.admin": {"title": "Retailer Admin"},
    "system.admin": {"title": "System Admin"}}


def permission_names():
    return PERMISSIONS.keys()


def permission_pairs():
    perms = [(n, v["title"]) for n, v in PERMISSIONS.items()]
    return perms


def permission_create(perm_type, perm_name, perm_receiver):
    if perm_type == "user":
        model = UserPermission
    elif perm_type == "group":
        model = GroupPermission
    else:
        raise ValueError("Invalid permission type requested")

    data = {perm_type + "_name": perm_receiver, "perm_name": perm_name}
    LOG.debug("PDATA %s" % data)
    return model(**data).save()


class Group(Base, GroupMixin):
    """
    An organization - typically something with users and customers
    """
    __format_string__ = "{group_name} ({organization_id})"
    __possible_permissions__ = permission_names()
    organization_id = Column(Integer)

    customers = relationship("Customer", backref="retailer")
    entities = relationship("Entity", backref="retailer")


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
    __format_string__ = "{first_name} {middle_name} {last_name}"
    __expose_attrs__ = ["first_name", "middle_name", "last_name"]
    __possible_permissions__ = permission_names()
    first_name = Column(UnicodeText)
    middle_name = Column(UnicodeText)
    last_name = Column(UnicodeText)


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
    __expose_attrs__ = ["brand", "model", "produced", "identifier"]
    __format_string__ = '{brand} {model} - {produced} {identifier}'
    id = Column(Integer, primary_key=True)
    type = Column(Unicode(50))
    brand = Column(UnicodeText)
    model = Column(UnicodeText)
    identifier = Column(UnicodeText, unique=True)
    produced = Column(Integer)

    retailer_id = Column(Integer, ForeignKey('groups.id'), nullable=False)

    @declared_attr
    def __mapper_args__(cls):
        name = unicode(camel_to_name(cls.__name__))
        return {"polymorphic_on": "type", "polymorphic_identity": name}


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
    __title_attrs__ = ["brand", "model", "produced", "identifier"]
    @property
    def gps(self, value=None):
        print "gps" in self.properties


class Car(DrivableEntity):
    pass


class Customer(Base):
    __format_string__ = "{name}"
    __tablename__ = "customer"
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText)
    organization_id = Column(Integer)
    contact = Column(UnicodeText)
    email = Column(UnicodeText)
    phone = Column(Integer)

    retailer_id = Column(Integer, ForeignKey('groups.id'))


class Location(Base):
    __expose_attrs__ = ["name", "street_address", "city", "postal_code"]
    __format_string__ = "{name} {street_name}  {city}"
    __tablename__ = "location"
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    street_address = Column(UnicodeText, nullable=False)
    city = Column(UnicodeText, nullable=False)
    postal_code = Column(Integer, nullable=False)

    retailer_id = Column(Integer, ForeignKey("groups.id"))
    retailer = relationship("Group", backref="locations")


class Booking(Base):
    __format_string__ = "{customer_name} - {start_date} > {end_date}"
    __expose_attrs__ = ["customer", "start", "end"]
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    price = Column(Integer)

    start_date = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False)
    start_location_id = Column(Integer)
    start_location = relationship(
        "Location",
        backref="bookings_start_here",
        primaryjoin="Booking.start_location_id==Location.id",
        foreign_keys=[start_location_id])

    end_date = Column(
        DateTime,
        default=lambda: datetime.datetime.utcnow() + datetime.timedelta(1),
        nullable=False)
    end_location_id = Column(Integer)
    end_location = relationship(
        "Location",
        backref="bookings_end_here",
        primaryjoin="Booking.end_location_id==Location.id",
        foreign_keys=[end_location_id])

    customer_id = Column(Integer, ForeignKey('customer.id'))
    customer = relationship("Customer", backref="orders")

    entity_id = Column(Integer, ForeignKey('entity.id'))
    entity = relationship("Entity", backref="orders")

    @property
    def start(self):
        return "{start_date} {start_location_name}".format(**self.format_data())

    @property
    def end(self):
        return "{end_date} {end_location_name}".format(**self.format_data())

    @classmethod
    def latest(cls, limit=5, time_since=1, filter_by={}):
        time_since = datetime.date.today() - datetime.timedelta(time_since)
        q = cls.query.filter(cls.created_at > time_since)
        q.filter_by(**filter_by)
        q.limit(limit)
        return q.all()


ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                    UserResourcePermission, GroupResourcePermission, Resource,
                    ExternalIdentity)
