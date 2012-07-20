from bookie.models.models import *
import re


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
            opts[key] = data[key]
    return filter_by, opts


def search_options(request):
    """
    Helper function that extracts filters from request.params and reached down
    into Model code and verifies them
    """
    filter_by, opts = _construct(request.params.copy())
    opts["filter_by"] = filter_by
    return opts
