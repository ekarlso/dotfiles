import ipdb
import logging
import re

import colander
import deform
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, CheckboxChoiceWidget, PasswordWidget, SequenceWidget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config
from sqlalchemy.orm import exc

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from .helpers import AddFormView, EditFormView, mk_form
from .helpers import PyramidGrid, column_link, wrap_td
from .helpers import menu_item, menu_came_from, get_nav_data
from .helpers import form



LOG = logging.getLogger(__name__)


def booking_actions(obj=None, request=None):
    data = get_nav_data(request)

    links = booking_links(obj, request)
    actions = []
    return links + actions


def booking_links(obj=None, request=None):
    data = get_nav_data(request)

    children = []
    children.append(menu_came_from(request))
    children.append({"value": "divider"})
    children.append(menu_item(_("Bookings"), "booking_overview", **data))
    children.append(menu_item(_("Create"), "booking_add", **data))
    return [{"value": "Navigation", "children": children}]


def customer_validate(node, value):
    request = get_current_request()
    try:
        models.Customer.get_by(name=value, retailer=request.group)
    except exc.NoResultFound:
        raise colander.Invalid(node, "Invalid Customer")


def entity_validate(node, value):
    request = get_current_request()
    try:
        models.Entity.get_by(name=value, retailer=request.group)
    except exc.NoResultFound:
        raise colander.Invalid(node, "Invalid entity")


def location_validate(node, value):
    request = get_current_request()
    try:
        models.Location.get_by(name=value, retailer=request.group)
    except exc.NoResultFound:
        raise colander.Invalid(node, "Invalid Location")



def pre_render(request, schema):
    """
    Helper to populate the schema
    """
    entities = []
    for e in models.Entity.all_by(retailer=request.group):
        entities.append(dict(label=str(e.name), value=str(e.name)))
    schema["entity"].widget.values = entities

    schema["customer"].widget.values = [dict(label=c.name, value=c.name) \
            for c in models.Customer.all_by(retailer=request.group)]

    locations = models.Location.all_by(retailer=request.group)
    location_data = [dict(label=l.name, value=l.name) for l in locations]
    schema["start_location"].widget.values = location_data
    schema["end_location"].widget.values = location_data
    return schema


def presave(obj, appstruct):
    appstruct["entity"] = models.Entity.get_by(
        name=appstruct["entity"], retailer=obj.request.group)

    appstruct["customer"] = models.Customer.get_by(
        name=appstruct["customer"], retailer=obj.request.group)

    appstruct["start_location"] = models.Location.by_name(
            appstruct["start_location"], obj.request.group)
    appstruct["end_location"] = models.Location.by_name(
            appstruct["end_location"], obj.request.group)

    return appstruct


class BookingSchema(colander.Schema):
    """
    A Schema for a booking
    """
    entity = colander.SchemaNode(
        colander.String(),
        validator=entity_validate,
        title=_("Entity to book"),
        widget=AutocompleteInputWidget())
    customer = colander.SchemaNode(
        colander.String(),
        validator=customer_validate,
        title=_("Customer"),
        widget=AutocompleteInputWidget())
    price = colander.SchemaNode(
        colander.Int(),
        title=_("Price"))
    start_location = colander.SchemaNode(
        colander.String(),
        validator=location_validate,
        title=_("Start location"),
        widget=AutocompleteInputWidget())
    start_at = colander.SchemaNode(
        colander.DateTime(None),
        title=_("Starts At"))
    end_location = colander.SchemaNode(
        colander.String(),
        validator=location_validate,
        title=_("End location"),
        widget=AutocompleteInputWidget())
    end_at = colander.SchemaNode(
        colander.DateTime(None),
        title=_("Ends time"))


class BookingAddForm(form.AddFormView):
    item_type = _(u"Booking")
    buttons = (Button("add_booking", _("Add Booking")),
                Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = BookingSchema()
        pre_render(self.request, schema)
        return schema

    def add_booking_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        presave(self, appstruct)
        obj = models.Booking().update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = self.request.route_url(
            "booking_overview", **get_nav_data(self.request))
        return HTTPFound(location=location)

    @property
    def cancel_url(self):
        return self.request.route_url("booking_overview",
                **get_nav_data(self.request))


class BookingForm(form.EditFormView):
    def schema_factory(self):
        schema = BookingSchema()
        pre_render(self.request, schema)
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("booking_overview",
                **get_nav_data(self.request))

    @property
    def success_url(self):
        return self.request.route_url("booking_overview",
                **get_nav_data(self.request))

    def save_success(self, appstruct):
        presave(self, appstruct)
        return super(BookingForm, self).save_success(appstruct)


@view_config(route_name="booking_add", permission="view",
            renderer="add.mako")
def booking_add(context, request):
    return mk_form(BookingAddForm, context, request,
        extra={"sidebar_data": booking_actions(request=request)})


@view_config(route_name="booking_manage", permission="view",
            renderer="booking_manage.mako")
def booking_manage(context, request):
    obj = models.Booking.get_by(id=request.matchdict["id"])

    form = mk_form(BookingForm, obj, request)
    if request.is_response(form):
        return form

    return {
        "sidebar_data": booking_actions(request=request),
        "form": form}


@view_config(route_name="booking_overview", permission="view",
            renderer="booking_overview.mako")
def booking_overview(context, request):
    deleted = request.params.get("deleted", False)

    bookings = models.Booking.search(
        filter_by={"deleted": deleted, "retailer": request.group})

    columns = ["id"] + models.Booking.exposed_attrs() + ["entity"]
    grid = PyramidGrid(bookings, columns, request=request, url=request.current_route_url)

    grid.exclude_ordering = ("id")
    grid.labels["id"] = ""

    grid.column_formats["entity"] = lambda cn, i, item: column_link(
        request, unicode(item.entity), "entity_view", url_kw=item.entity.to_dict())

    grid.column_formats["id"] = lambda cn, i, item: column_link(
        request, "Manage", "booking_manage", url_kw=item.to_dict())

    return {
        "sidebar_data": booking_actions(request=request),
        "booking_grid": grid}


def includeme(config):
    config.add_route("booking_add", "/g,{group}/booking/add")
    config.add_route("booking_manage", "/g,{group}/booking/{id}")
    config.add_route("booking_overview", "/g,{group}/booking")
