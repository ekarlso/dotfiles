from sqlalchemy.types import TypeDecorator, Unicode
import json


def dump_default(obj):
    if isinstance(obj, MutationDict):
        return obj._d
    elif isinstance(obj, MutationList):
        return obj._d


class JSONType(TypeDecorator):
    """http://www.sqlalchemy.org/docs/core/types.html#marshal-json-strings"""
    impl = Unicode

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value, default=dump_default)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value
