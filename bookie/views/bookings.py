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

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from .helpers import AddFormView, EditFormView, mk_form
from .helpers import PyramidGrid, column_link, wrap_td
from .helpers import menu_item, menu_came_from, get_nav_data, get_url, create_anchor



LOG = logging.getLogger(__name__)


def booking_actions(obj=None, request=None):
    menu = [] + booking_links(obj, request)
    return menu


def booking_links(obj=None, request=None):
    data = get_nav_data(request)

    nav_children = []
    nav_children.append(menu_came_from(request))
    nav_children.append({"value": "divider"})
    nav_children.append(menu_item(_("Bookings"), "booking_overview", **data))
    nav_children.append(menu_item(_("Create"), "booking_add", **data))
    navigation = [{"value": "Navigation", "children": nav_children}]
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
        return BookingSchema()

    def add_booking_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        obj = models.Booking().update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = get_url("entities_view", type=self.item_type.lower())
        return HTTPFound(location=location)


class BookingEditForm(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return BookingSchema()


@view_config(route_name="booking_add", permission="view",
            renderer="add.mako")
def booking_add(context, request):
    return mk_form(BookingAddForm, context, request,
        extra={"sidebar_data": booking_actions(request=request)})


@view_config(route_name="booking_edit", permission="edit",
            renderer="edit.mako")
def booking_edit(context, request):
    obj = models.Order.filter_by(
        deleted=False, id=request.matchdict["id"]).one()
    return mk_form(BookingEditForm, obj, request,
        extra=dict(sidebar_data=booking_actions(request=request)))


@view_config(route_name="booking_view", permission="view",
            renderer="view.mako")
def booking_view(context, request):
    obj = models.Booking.get_by(id=request.matchdict["id"])
    return {
        "sidebar_data": booking_actions(request=request),
        "booking": obj}


@view_config(route_name="booking_overview", permission="view",
            renderer="booking_overview.mako")
def booking_overview(context, request):
    deleted = request.params.get("deleted", False)

    bookings = models.Booking.search(
        filter_by={"deleted": deleted, "retailer": request.group})

    columns = models.Booking.exposed_attrs() + ["entity"]
    grid = PyramidGrid(bookings, columns)

    grid.column_formats["entity"] = lambda cn, i, item: column_link(
        request, item["entity"], "entity_view", view_kw=item.entity.to_dict())

    return {
        "sidebar_data": booking_actions(request=request),
        "booking_grid": grid}


def includeme(config):
    config.add_route("booking_add", "/@{group}/booking/add")
    config.add_route("booking_edit", "/@{group}/booking/{id}/edit")
    config.add_route("booking_view", "/@{group}/booking/{id}/view")
    config.add_route("booking_overview", "/@{group}/booking")
