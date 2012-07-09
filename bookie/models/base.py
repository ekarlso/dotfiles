from datetime import datetime
import logging

from colanderalchemy import SQLAlchemyMapping
from sqlalchemy import Column, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import class_mapper, object_mapper, scoped_session, sessionmaker
from sqlalchemy.orm.properties import ColumnProperty, RelationshipProperty
from zope.sqlalchemy import ZopeTransactionExtension


LOG = logging.getLogger(__name__)


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))


def get_session():
    return DBSession


def get_prop_names(obj, exclude=[]):
    local, remote = [], []
    for p in obj.__mapper__.iterate_properties:
        if p.key not in exclude:
            if isinstance(p, ColumnProperty):
                local.append(p.key)
            if isinstance(p, RelationshipProperty):
                remote.append(p.key)
    return local, remote



class BaseModel(object):
    """
    Base class to make ones life working with models and python easier
    """
    __expose_attrs__ = None

    __table_args__ = {"mysql_engine": "InnoDB"}
    __table__initialized__ = False
    __protected_attributes__ = set([
        "created_at", "updated_at", "deleted_at", "deleted"])

    created_at = Column(DateTime, default=datetime.utcnow,
        nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
        nullable=False, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)
    deleted = Column(Boolean, nullable=False, default=False)

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
            self[k] = v
        return self

    def next(self):
        n = self._i.next().name
        return n, getattr(self, n)

    def keys(self):
        return [k for k in self.__dict__.keys()]

    def values(self, attrs=None):
        return self.__dict__.values()

    def items(self):
        return dict([(k, getattr(self, k)) for k in self])

    @classmethod
    def get_by(cls, *args, **kw):
        """
        Get one by filters
        """
        return cls.query.filter_by(*args, **kw).one()

    @classmethod
    def all_by(cls, *args, **kw):
        """
        Get all by filters
        """
        return cls.query.filter_by(*args, **kw).all()

    @classmethod
    def _search_query(cls, filters=[], filter_by={}, limit=10):
        """
        A Search helper method

        :key filters: Filters to apply
        :key limit: Limit to apply
        """
        q = cls.query.filter_by(**filter_by)
        q = q.filter(*filters)
        if limit:
            q.limit(limit)
        return q

    @classmethod
    def search(cls, **kw):
        """
        Helper for searching, get it?

        See _search_query keywords
        """
        return cls._search_query(**kw).all()

    def to_dict(self, deep={}, exclude=[]):
        """
        Make a dict of the object

        :key deep: A dict containing what to expand on the attribute
        :key exclude: What to excluse on the remote attribute
        """
        data = dict([(k, getattr(self, k)) \
            for k in get_prop_names(self, exclude=exclude)[0]])

        for rname, rdeep in deep.items():
            data.update(self.remote_to_dict(rname, rdeep))
        return data

    def remote_to_dict(self, attr, deep={}, exclude=[]):
        """
        This is basically a part of "Elixir's" to_dict method.
        I took it out into remote_to_dict to be able to use it elsewhere as
        well.

        See 'self.to_dict' for 'deep' and 'exclude'

        :param attr: The remote attribute to dict
        """
        data = {}
        db_data = getattr(self, attr)
        #FIXME: use attribute names (ie coltoprop) instead of column names
        fks = self.__mapper__.get_property(attr).remote_side
        exclude = exclude + [c.name for c in fks]

        def is_dictable(obj):
            return hasattr(obj, "to_dict")

        if db_data is None:
            data[attr] = None
        elif isinstance(db_data, list):
            data[attr] = [row.to_dict(deep=deep, exclude=exclude) \
                for row in db_data if is_dictable(row)]
        else:
            if is_dictable(db_data):
                data[attr] = db_data.to_dict(deep=deep, exclude=exclude)
        return data

    @classmethod
    def exposed_attrs(cls):
        """
        Returns the either given or attrs set in __exposed_attrs__
        """
        attrs = cls.__expose_attrs__
        if not attrs and isinstance(cls, BaseModel):
            attrs = attrs.keys()
        return list(attrs)

    def format_data(self):
        """
        Method to make some data for formatting.

        It will take self.to_dict and merge in data from the first level of
        relations like:
        Booking.price
        Booking.start_location

        Becomes:
        {"price": 1, "start_location_name": "Stavanger"}

        This to have more data to format on
        """
        local, remote = get_prop_names(self)
        data = self.to_dict()
        for remote_property in remote:
            remote_data = self.remote_to_dict(remote_property)
            for relation_key, relation_value in remote_data.items():
                if isinstance(relation_value, dict):
                    for k, v in relation_value.items():
                        data["%s_%s" % (relation_key, k)] = v
        return data

    def format_self(self, format_string=None):
        """
        Represent ourselves

        :key format_string: Optionally override self.__format_string__
        """
        format = format_string or self.__format_string__
        return format.format(**self.format_data())

    @property
    def title(self):
        """
        Calls self.format_self()
        """
        return self.format_self()

    def __unicode__(self):
        """
        Does the same as self.title()
        """
        return self.format_self()

    @classmethod
    def get_schema(cls):
        """
        If using ColandarAlchemy this will wrap a mapping around me
        """
        return SQLAlchemyMapping(cls)

    def from_dict(self, data):
        """
        Update a mapped class with data from a JSON-style nested
        dict/list

        :param data: Data to load
        """
        mapper = object_mapper(self)
        for key, value in data.items():
            if isinstance(value, dict):
                dbvalue = getattr(self, key)
                rel_class = mapper.get_property(key).mapper.class_
                pk_props = rel_class.__mapper__.primary_key

                # If the data doesn't contain any pk, and the relationship
                # already has a value, update that record.
                if not [1 for p in pk_props if p.key in data] and \
                        dbvalue is not None:
                    dbvalue.from_dict(value)
                else:
                    record = rel_class.update_or_create(value)
                    setattr(self, key, record)
            elif isinstance(value, list) and \
                    value and isinstance(value[0], dict):
                rel_class = mapper.get_property(key).mapper.class_
                new_attr_value = []
                for row in value:
                    if not isinstance(row, dict):
                        raise Exception(
                            'Cannot send mixed (dict/non dict) data '
                            'to list relationships in from_dict data.')
                    record = rel_class.update_or_create(row)
                    new_attr_value.append(record)
                setattr(self, key, new_attr_value)
            else:
                setattr(self, key, value)
        return self

    @classmethod
    def update_or_create(cls, data, surrogate=True):
        """
        Update or create a record

        :param data: Data to use
        """
        pk_props = cls.__mapper__.primary_key
        # if all pk are present and not None
        if not [1 for p in pk_props if data.get(p.key) is None]:
            pk_tuple = tuple([data[prop.key] for prop in pk_props])
            record = cls.query.get(pk_tuple)
            if record is None:
                if surrogate:
                    raise Exception("cannot create surrogate with pk")
                else:
                    record = cls()
        else:
            if surrogate:
                record = cls()
            else:
                raise Exception("cannot create non surrogate without pk")
        record.from_dict(data)
        return record


Base = declarative_base(cls=BaseModel)
Base.query = DBSession.query_property()


__all__ = ["DBSession", "Base"]
