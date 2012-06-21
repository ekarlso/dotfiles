import logging
import pdb

import colander
import deform
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, CheckboxChoiceWidget, PasswordWidget, SequenceWidget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.view import view_config

from ..db import models
from ..utils import _, camel_to_name, name_to_camel
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import menu_item, menu_came_from, get_url, create_anchor, wrap_td


LOG = logging.getLogger(__name__)


def booking_actions(obj=None, request=None):
    menu = [] + booking_links(obj, request)
    return menu


def booking_links(obj=None, request=None):
    nav_children = []
    nav_children.append(menu_item(_("Bookings"), "bookings_view"))
    nav_children.append(menu_item(_("Create"), "booking_add"))
    nav_children.append("spacer")
    nav_children.append(menu_came_from(request))
    navigation = [{"title": "Navigation", "children": nav_children}]
    return navigation


class BookingSchema(colander.Schema):
    price = colander.SchemaNode(
        colander.Int(),
        title=_("Price"))
    end_at = colander.SchemaNode(
        colander.DateTime(),
        title=_("Ends At"))
    start_at = colander.SchemaNode(
        colander.DateTime(),
        title=_("Starts At"))


class BookingAddForm(AddFormView):
    item_type = _(u"Booking")
    buttons = (Button("add_booking", _("Add Booking")),
                Button("cancel", _("Cancel")))

    def schema_factory(self):
        #return models.Booking.get_schema()
        return BookingSchema()

    def add_booking_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        obj = models.Booking().update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = get_url("entities_view", type=self.item_type.lower())
        return HTTPFound(location=location)


@view_config(route_name="booking_add", permission="view",
            renderer="booking/add.mako")
def booking_add(context, request):
    form = mk_form(BookingAddForm, context, request)
    return {"navtree": booking_actions(request=request), "form": form}


@view_config(route_name="booking_view", permission="view",
            renderer="booking/view.pt")
def booking_view(context, request):
    return {"navtree": booking_actions(request=request), "form": ""}


@view_config(route_name="bookings_view", permission="view",
            renderer="booking/overview.pt")
def bookings_view(context, request):
    return {"navtree": booking_actions(request=request), "form": ""}


def includeme(config):
    config.add_route("booking_add", "/booking/add")
    config.add_route("booking_edit", "/booking/{id}/edit")
    config.add_route("booking_view", "/booking/{id}/view")
    config.add_route("bookings_view", "/booking")
