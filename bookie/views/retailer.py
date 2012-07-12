import logging

import colander
import deform

from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, PasswordWidget, SequenceWidget, TextAreaWidget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.view import view_config

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import menu_item, get_nav_data, \
    wrap_td
from . import helpers, users


def sidebar_links(request):
    d = get_nav_data(request)
    links = []
    links.append({"value": "Dashboard", "route": "retailer_home",
        "url_kw": d})
    links.append({"value": "Settings", "route": "retailer_settings",
        "url_kw": d})
    return [{"value": "Navigation", "children": links}]


def quick_links(request):
    d = get_nav_data(request)
    links = []
    links.append({"icon": "plus", "value": _("New Booking"),
        "route": "booking_add", "url_kw": d})
    links.append({"value": _("New Entity"), "icon": "plus",
        "route": "entity_add", "url_kw": d})
    links.append({"value": _("Invite User"), "icon": "plus",
        "route": "retailer_invite_user", "url_kw": d})
    return {"children": links}


class InviteSchema(colander.Schema):
    user_name = colander.SchemaNode(
        colander.String(),
        title=_("User to invite"))
    user_permissions = colander.SchemaNode(
            deform.Set(allow_empty=True),
            validator=users.roleset_validator,
            missing=[],
            widget=CheckboxChoiceWidget(),
            title=_("Permissions"))
    message = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(max=300),
            widget=TextAreaWidget(rows=10, cols=60),
            title=_("Invititational message"))


class InviteForm(helpers.AddFormView):
    item_type = "Invite"

    def schema_factory(self):
        s = InviteSchema()
        s["user_permissions"].widget.values = \
                models.permission_pairs(models.PERMISSIONS)
        return InviteSchema()

    def add_invite_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        return HTTPFound(location=request.route("retailer_home",
            group=request.group))


@view_config(route_name="retailer_home", permission="view",
            renderer="retailer_home.mako")
def home(context, request):
    return {"sidebar_data": sidebar_links(request), "nav_quick": quick_links(request)}


@view_config(route_name="retailer_settings", permission="admin",
            renderer="retailer_settings.mako")
def settings(context, request):
    return {"sidebar_data": sidebar_links(request)}


@view_config(route_name="retailer_invite_user", permission="admin",
            renderer="retailer_invite.mako")
def invite(context, request):
    """
    Ivite a User to join this retailer.
    Simply give membership if the user is already registered.
    """
    form = mk_form(InviteForm, context, request)
    return {"form": form}


def includeme(config):
    config.add_route("retailer_home", "/g,{group}")
    config.add_route("retailer_invite_user", "/g,{group}/user/invite")
    config.add_route("retailer_settings", "/g,{group}/settings")
