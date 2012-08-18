# vim: tabstop=4 shiftwidth=4 softtabstop=4

import re
import sys
import datetime
import logging
from pprint import pformat
from UserDict import UserDict

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.sql.expression import cast
from sqlalchemy.orm import relationship, backref, exc, object_mapper, \
    synonym, validates
from sqlalchemy import Column, Integer, Unicode, BigInteger, \
    Unicode, ForeignKey, Date, DateTime, Boolean, UnicodeText, UniqueConstraint, Table
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from ziggurat_foundations.models import BaseModel, UserMixin, GroupMixin, \
    GroupPermissionMixin, UserGroupMixin, GroupResourcePermissionMixin, \
    ResourceMixin, UserPermissionMixin, UserResourcePermissionMixin, \
    ExternalIdentityMixin
from ziggurat_foundations import ziggurat_model_init, models as zm

from .. import redis, utils
from .base import Base, MetadataMixin, DBSession
from .types import JSONType


LOG = logging.getLogger(__name__)

zm.DBSession = DBSession


SECURITY_PERMISSIONS = [
    ("admin", {"title": "Admin", "description": "Admin privileges"})
]

PERMISSIONS = SECURITY_PERMISSIONS

STATUS = {
    0: "unread",
    1: "read"
}


ENTITY = r"^(?P<brand>\S+): (?P<model>\S+) - " + \
        "(?P<produced>\d{4}) - (?P<identifier>\S+)$"


def permission_names(permissions):
    return [p[0] for p in permissions]


def permission_pairs(permissions):
    return [(n, v["title"]) for n, v in permissions]


def permission_create(perm_type, perm_name, perm_receiver):
    if perm_type == "user":
        model = UserPermission
    elif perm_type == "group":
        model = GroupPermission
    else:
        raise ValueError("Invalid permission type requested")

    data = {perm_type + "_name": perm_receiver, "perm_name": perm_name}
    return model(**data)


class Group(Base, GroupMixin):
    """
    An organization - typically something with users and customers
    """
    __format_string__ = "{group_name}"
    __expose_attrs__ = ["group_name"]
    __possible_permissions__ = permission_names(PERMISSIONS)

    _group_type = Column("group_type", Unicode(20), nullable=False)
    uuid = Column(Unicode(36), default=utils.generate_uuid)

    @declared_attr
    def __mapper_args__(cls):
        name = unicode(utils.camel_to_name(cls.__name__))
        return {"polymorphic_on": "_group_type", "polymorphic_identity": name}

    @hybrid_property
    def group_type(self):
        return self._group_type

    @group_type.setter
    def group_type_set(self, value):
        self._group_type = value


class Retailer(Group):
    __tablename__ = "groups_retailer"

    organization_id = Column(Unicode(40))
    id = Column(Integer, ForeignKey("groups.id",
                        onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)

    customers = relationship("Customer", backref="retailer")
    entities = relationship("Entity", backref="retailer")

    def __repr__(self):
        return self.group_name


class SecurityGroup(Group):
    __tablename__ = "groups_security"
    __possible_permissions__ = permission_names(PERMISSIONS)
    id = Column(Integer, ForeignKey("groups.id",
                        onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)


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
    __format_string__ = "resource_name"
    __expose_attrs__ = ["resource_name", "description"]

    @declared_attr
    def parent(self):
        return relationship("Resource", backref="children",
                                    remote_side="Resource.resource_id")

    @declared_attr
    def __mapper_args__(cls):
        name = unicode(utils.camel_to_name(cls.__name__))
        return {"polymorphic_on": "resource_type", "polymorphic_identity": name}


class UserGroup(Base, UserGroupMixin):
    """
    Map a User to a Group
    """
    pass


class User(Base, UserMixin):
    __format_string__ = "{first_name} {middle_name} {last_name}"
    __expose_attrs__ = ["first_name", "middle_name", "last_name"]
    __possible_permissions__ = permission_names(PERMISSIONS)
    first_name = Column(UnicodeText, default=u'')
    middle_name = Column(UnicodeText, default=u'')
    last_name = Column(UnicodeText, default=u'')

    current_group = relationship("Group", uselist=False)
    current_group_id = Column(Integer, ForeignKey("groups.id"))

    message_associations = relationship("MessageAssociation", backref=backref("user", lazy="joined"))

    def __unicode__(self):
        return str(self.display_name)

    @hybrid_property
    def display_name(self):
        if not re.search("^(\s+|)$", self.full_name):
            name = self.full_name + ": " + self.user_name
        else:
            name = self.user_name
        return name

    @hybrid_property
    def full_name(self):
        return self.first_name + " " + self.middle_name + " " + self.last_name

    @property
    def retailers(self):
        return [g for g in self.groups if g.group_type == "retailer"]

    def is_current_group(self, group):
        return group.id == self.current_group_id \
                if self.current_group_id else False

    def has_group(self, id_, group_type="retailer"):
        count = self.groups_dynamic.filter_by(
                id=id_, group_type=group_type).count()
        return True and count == 1 or False



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


class Event(Base):
    """
    An event in the system like a User invite or similar
    """
    __tablename__ = "events"
    id = Column(Unicode(36), default=utils.generate_uuid, primary_key=True)
    data = Column(JSONType())

    group_id = Column(Integer, ForeignKey("groups.id",
                    onupdate="CASCADE", ondelete="CASCADE"))
    group = relationship("Group", backref="events")

    user_id = Column(Integer, ForeignKey("users.id",
                    onupdate="CASCADE", ondelete="CASCADE"))
    user = relationship("User", backref="events")


class MessageAssociation(Base):
    """
    A Mapping of pr user data towards the message
    """
    __tablename__ = "message_associations"

    _status = Column("status", Integer, default=0)
    extra = Column(JSONType())

    user_id = Column(Integer, ForeignKey("users.id",
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)

    message_id = Column(Unicode(36), ForeignKey("messages.id",
        onupdate="CASCADE", ondelete="CASCADE"), primary_key=True)
    message = relationship("Message", backref=backref("associations", lazy="joined"))

    @hybrid_property
    def status(self):
        return STATUS[self._status]

    @status.setter
    def status_set(self, value):
        assert value in STATUS.values(), True


class Message(Base):
    """
    A Message that simply holds the content of the message for now.
    """
    __tablename__ = "messages"
    id = Column(Unicode(36), default=utils.generate_uuid, primary_key=True)
    content = Column(UnicodeText)
    extra = Column(JSONType())

    sender_id = Column(Integer, ForeignKey("users.id"))
    sender = relationship("User", backref="messages")

    @property
    def short(self):
        """
        Return the messages contents in short.
        """
        return self.content[-40:] + "..."

    @property
    def receivers(self):
        """
        Returns all of the receivers
        """
        return [assoc.user for assoc in self.associations]

    @property
    def receivers_string(self):
        """
        Return a string of receivers
        """
        return ", ".join([u.display_name for u in self.receivers])

    def user_is_recipient(self, user):
        """
        Expression to see if a user is a receiver
        """
        return user in self.receivers


category_entity_associations = Table(
    'category_entity_assocations', Base.metadata,
    Column('category_id', Integer, ForeignKey('resources.resource_id')),
    Column('entity_id', Unicode(36), ForeignKey('entities.id'))
)


class Category(Resource):
    """
    A entity category is owned by a retailer
    """
    __tablename__ = "categories"
    __expose_attrs__ = ["resource_name", "description"]
    __format_string__ = "{resource_name}"
    description = Column(UnicodeText)

    resource_id = Column(Integer, ForeignKey("resources.resource_id",
                        onupdate='CASCADE', ondelete='CASCADE'),
                        primary_key=True)

    entities = relationship("Entity", secondary=category_entity_associations,
                            backref="categories")


category_metadata_associations = Table(
    'category_metadata_assications', Base.metadata,
    Column('category_id', Integer, ForeignKey('resources.resource_id')),
    Column('metadata_id', Unicode(36), ForeignKey('category_metadata.id'))
)


class CategoryMeta(Base):
    __tablename__ = "category_metadata"
    __expose_attrs__ = ["name", "value"]
    id = Column(Unicode(36), primary_key=True, default=utils.generate_uuid)
    name = Column(Unicode(60), index=True, nullable=False)
    value = Column(UnicodeText, nullable=True)


class Entity(Base, MetadataMixin):
    """
    A Entity is a product / thing to be rented out to a customer
    """
    __tablename__ = "entities"
    __expose_attrs__ = ["brand", "model", "produced", "identifier", "color"]
    __format_string__ = '{brand}: {model} - {produced} - {identifier}'
    id = Column(Unicode(36), primary_key=True, default=utils.generate_uuid)
    type = Column(Unicode(40))
    brand = Column(Unicode(100))
    model = Column(Unicode(100))
    produced = Column(Integer)
    identifier = Column(Unicode(100))

    # NOTE: Change to Int and ID
    retailer_id = Column(Integer, ForeignKey('groups.id'))

    @declared_attr
    def __mapper_args__(cls):
        name = unicode(utils.camel_to_name(cls.__name__))
        return {"polymorphic_on": "type", "polymorphic_identity": name}

    @hybrid_property
    def name(self):
        return self.brand + ": " + self.model + " - " + str(self.produced) + " - " \
                + self.identifier

    @name.expression
    def name_expr(self):
        return self.brand + ": " + self.model + " - " + cast(self.produced, Unicode) + " - " \
                + self.identifier

    @name.setter
    def name_set(self, value):
        data = re.match(ENTITY, value).groupdict()
        self.update(data)

    def get_color(self):
        return self.meta_by_key("color")

    def set_color(self, value):
        return self.set_meta({"color": value})

    color = property(get_color, set_color)


class EntityMetadata(Base):
    __tablename__ = "entity_metadata"
    id = Column(Unicode(36), primary_key=True, default=utils.generate_uuid)
    key = Column(Unicode(60), index=True, nullable=False)
    value = Column(UnicodeText, nullable=True)

    entity_id = Column(Unicode(36), ForeignKey("entities.id"))
    entity = relationship("Entity", backref=backref("metadata", lazy='dynamic'))


class DrivableEntity(Entity):
    """
    Represent a drivable entity
    """
    @property
    def gps(self, value=None):
        print "gps" in self.properties


class Car(DrivableEntity):
    pass


class Customer(Base):
    __expose_attrs__ = ["name", "organization_id", "contact", "email", "phone"]
    __format_string__ = "{name}"
    __tablename__ = "customers"
    id = Column(Unicode(36), primary_key=True, default=utils.generate_uuid)
    name = Column(Unicode(40))
    organization_id = Column(Unicode(60))
    contact = Column(UnicodeText)
    email = Column(Unicode(40))
    phone = Column(Unicode(40))

    # NOTE: Change to Int and ID
    retailer_id = Column(Integer, ForeignKey('groups.id',
                    onupdate="CASCADE", ondelete="CASCADE"))


class Location(Base):
    __expose_attrs__ = ["city", "address", "postal_code"]
    __format_string__ = "{city}: {address}"
    __tablename__ = "locations"
    id = Column(Unicode(36), primary_key=True, default=utils.generate_uuid)
    address = Column(UnicodeText, nullable=False)
    city = Column(UnicodeText, nullable=False)
    postal_code = Column(Integer, nullable=False)

    # NOTE: Change to Int and ID
    retailer_id = Column(Integer, ForeignKey("groups.id"))
    retailer = relationship("Group", backref="locations")

    @hybrid_property
    def name(self):
        return self.city + ": " + self.address

    @classmethod
    def by_name(cls, name, retailer=None):
        q = cls.query.filter(cls.name==name)
        if retailer:
            q = q.filter_by(retailer=retailer)
        return q.one()


entity_booking_assocations = Table('entity_booking_assocations', Base.metadata,
    Column('entity_id', Unicode(36), ForeignKey('entities.id')),
    Column('bookings_id', Unicode(36), ForeignKey('bookings.id'))
)


class Booking(Base):
    __format_string__ = "{customer_name} - {start_at} > {end_at}"
    __expose_attrs__ = ["customer", "start_location", "start_at", "end_location", "end_at"]
    __tablename__ = "bookings"
    id = Column(Unicode(36), primary_key=True, default=utils.generate_uuid)
    price = Column(Integer)

    start_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        nullable=False)
    start_location_id = Column(Unicode(36))
    start_location = relationship(
        "Location",
        backref=backref("bookings_start_here", lazy="joined"),
        primaryjoin="Booking.start_location_id==Location.id",
        foreign_keys=[start_location_id])

    end_at = Column(
        DateTime,
        default=lambda: datetime.datetime.utcnow() + datetime.timedelta(1),
        nullable=False)
    end_location_id = Column(Unicode(36))
    end_location = relationship(
        "Location",
        backref=backref("bookings_end_here", lazy="joined"),
        primaryjoin="Booking.end_location_id==Location.id",
        foreign_keys=[end_location_id])

    customer_id = Column(Unicode(36), ForeignKey('customers.id'))
    customer = relationship("Customer", backref="bookings")

    entities = relationship("Entity", secondary=entity_booking_assocations,
            backref="bookings")

    @property
    def entities_string(self):
        return ", ".join([e.display_name for e in self.entities])

    @property
    def entities_count(self):
        return len(self.entities)

    @classmethod
    def _search(cls, filter_by={}, query=None, *args, **kw):
        """
        Search bookings

        :param retailer: Narrow this search down to a certain retailer
        """
        query = query or cls.query

        # NOTE:
        retailer = filter_by.pop("retailer", None)
        if retailer:
            # NOTE: Booking is linked to a Customer which is linked to a
            #       Retailer group
            # TODO: Change to Customer.retailer_id
            query = query.filter_by(customer_id=Customer.id).\
                        join(Customer).filter(Customer.retailer==retailer)

        query = super(Booking, cls)._search(*args, filter_by=filter_by, query=query, **kw)
        return query

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
