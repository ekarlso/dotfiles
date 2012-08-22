from pyramid.request import Request
import re

from bookie.models.models import *

def _construct(data):
    def _fkey(key):
        if key in ("limit") or re.search("order_(col|dir)", key):
            return False
        else:
            return True

    filter_by = {}
    for key, value in data.items():
        if _fkey(key):
            filter_by[key] = value

    opts = {}
    for key in ["order_col", "order_dir", "limit", "marker_id"]:
        if key in data:
            value = data[key]
            if key == "order_dir" and value == "dsc":
                value = "desc"
            opts[key] = value
    return filter_by, opts


def search_options(obj):
    """
    Helper function that extracts filters from request.params and reached down
    into Model code and verifies them
    """
    params = obj.params.copy() if isinstance(obj, Request) else obj
    params.pop("account", None)
    filter_by, opts = _construct(params)
    opts["filter_by"] = filter_by
    return opts
