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


def sidebar_links(request):
    d = get_nav_data(request)
    links = []
    links.append({"value": "Dashboard", "view": "retailer_dashboard",
        "view_kw": d})
    return [{"value": "Navigation", "children": links}]


def quick_links(request):
    d = get_nav_data(request)

    links = []
    links.append({"icon": "plus", "value": _("New Booking"),
        "view": "booking_add", "view_kw": d})
    links.append({"value": _("New Entity"), "icon": "plus",
        "view": "entity_add", "view_kw": d})
    links.append({"value": _("New User"), "icon": "plus",
        "view": "tenant_user_add", "view_kw": d})
    return {"children": links}


@view_config(route_name="retailer_dashboard", renderer="retailer_dashboard.mako")
def dashboard(context, request):
    return {"nav_data": sidebar_links(request), "nav_quick": quick_links(request)}


def includeme(config):
    config.add_route("retailer_dashboard", "/@{group}/dashboard")
