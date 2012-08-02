from datetime import datetime
import logging

from colanderalchemy import SQLAlchemyMapping
import sqlalchemy as sqla
import sqlalchemy.orm
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
    __format_string__ = None

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
        return [k for k in self.__dict__.keys() if not k.startswith("_sa")]

    def values(self, attrs=None):
        return self.__dict__.values()

    def items(self):
        return dict([(k, getattr(self, k)) for k in self.keys()])

    # NOTE: Search alike stuff below here
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

    @staticmethod
    def paginate_query(query, model, limit, order_cols, marker=None,
            order_dir=None, order_dirs=None):
        """
        Pagination helper borrowed from OpenStack Glance code

        Pagination works by requiring a unique sort_key, specified by sort_keys.
        (If sort_keys is not unique, then we risk looping through values.)
        We use the last row in the previous page as the 'marker' for pagination.
        So we must return values that follow the passed marker in the order.
        With a single-valued sort_key, this would be easy: sort_key > X.
        With a compound-values sort_key, (k1, k2, k3) we must do this to repeat
        the lexicographical ordering:
            (k1 > X1) or (k1 == X1 && k2 > X2)
            (k1 == X1 && k2 == X2 && k3 > X3)

        We also have to cope with different sort_directions.

        Typically, the id of the last row is used as the client-facing pagination
        marker, then the actual marker object must be fetched from the db and
        passed in to us as marker.

        :param query: the query object to which we should add paging/sorting
        :param model: the ORM model class
        :param limit: maximum number of items to return
        :param sort_keys: array of attributes by which results should be sorted
        :param marker: the last item of the previous page; we returns the next
                results after this value.
        :param sort_dir: direction in which results should be sorted (asc, desc)
        :param sort_dirs: per-column array of sort_dirs, corresponding to sort_keys

        :rtype: sqlalchemy.orm.query.Query
        :return: The query with sorting/pagination added.
        """
        if 'id' not in order_cols:
            LOG.warn(_('Id not in sort_keys; is sort_keys unique?'))

        assert(not (order_dir and order_dirs))

        # Default the sort direction to ascending
        if order_dirs is None and order_dir is None:
            order_dir = 'asc'

        # Ensure a per-column sort direction
        if order_dirs is None:
            order_dirs = [order_dir for _order_col in order_cols]

        assert(len(order_dirs) == len(order_cols))

        # Add sorting
        for current_order_col, current_order_dir in zip(order_cols, order_dirs):
            order_dir_func = {
                'asc': sqlalchemy.asc,
                'desc': sqlalchemy.desc,
            }[current_order_dir]

            try:
                order_col_attr = getattr(model, current_order_col)
            except AttributeError:
                raise AtributeError("Invalid order column")
            query = query.order_by(order_dir_func(order_col_attr))

        # Add pagination
        if marker is not None:
            marker_values = []
            for order_col in order_cols:
                v = getattr(marker, order_col)
                marker_values.append(v)

            # Build up an array of sort criteria as in the docstring
            criteria_list = []
            for i in xrange(0, len(order_cols)):
                crit_attrs = []
                for j in xrange(0, i):
                    model_attr = getattr(model, order_cols[j])
                    crit_attrs.append((model_attr == marker_values[j]))

                model_attr = getattr(model, order_cols[i])
                if order_dirs[i] == 'desc':
                    crit_attrs.append((model_attr < marker_values[i]))
                elif order_dirs[i] == 'asc':
                    crit_attrs.append((model_attr > marker_values[i]))
                else:
                    raise ValueError(_("Unknown sort direction, "
                        "must be 'desc' or 'asc'"))

                criteria = sqlalchemy.sql.and_(*crit_attrs)
                criteria_list.append(criteria)

            f = sqlalchemy.sql.or_(*criteria_list)
            query = query.filter(f)

        if limit is not None:
            query = query.limit(limit)

        return query

    @classmethod
    def _prepare_search(cls, filters=[], filter_by={}, marker_id=None,
            limit=10, order_col="created_at", order_dir="desc", query=None):
        """
        A Search helper method

        :key filters: List / Set of filter expressions to use
        :key filter_by: Set of filter_by keywords
        :key marker: A marker ID
        :key limit: Limit to apply
        :key order_col: What column to order by
        :key order_dir: Which direction

        :key query: Override query
        """
        query = query or cls.query

        query = query.filter(*filters)
        query = query.filter_by(**filter_by)

        marker_obj = None
        if marker_id is not None:
            marker_obj = cls.get_by(id=marker_id)

        # NOTE: Add pagination!!
        query = cls.paginate_query(query, cls, limit,
            [order_col, "created_at", "id"], marker=marker_obj,
            order_dir=order_dir)
        return query

    @classmethod
    def search(cls, *args, **kw):
        """
        Helper for searching, get it?

        See _prepare_search keywords
        """
        return cls._prepare_search(*args, **kw).all()

    # NOTE: Format helpers below here
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
        return format.format(**self.format_data()) if format else None

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

    # NOTE: Utility functions below
    @classmethod
    def get_schema(cls):
        """
        If using ColandarAlchemy this will wrap a mapping around me
        """
        return SQLAlchemyMapping(cls)

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
