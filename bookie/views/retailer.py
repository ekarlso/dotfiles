import logging

import colander
import deform

from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, CheckboxChoiceWidget, PasswordWidget, SequenceWidget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.view import view_config

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import menu_item, get_nav_data, get_url, create_anchor, \
    wrap_td


def links(request):
    d = get_nav_data(request)
    c = []
    c.append({"value": "Dashboard", "view_name": "retailer_dashboard",
        "view_kw": d})
    return [{"value": "Navigation", "children": c}]


@view_config(route_name="retailer_dashboard", renderer="retailer_dashboard.mako")
def dashboard(context, request):
    return {"navtree": links(request)}


def includeme(config):
    config.add_route("retailer_dashboard", "/@{group}/dashboard")
