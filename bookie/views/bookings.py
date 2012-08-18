import logging
import re

import colander
import deform
import deform_bootstrap.widget as db_widget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config
import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from . import helpers as h, search



LOG = logging.getLogger(__name__)


def booking_actions(request, obj=None):
    data = h.get_nav_data(request)

    links = booking_links(request, obj)
    actions = []
    actions.append({"value": "Manage", "route": "booking_manage",
        "url_kw": data})
    return links + [{"value": "Actions", "children": actions}]


def booking_links(request, obj=None):
    data = h.get_nav_data(request)

    links = []
    links.append(h.menu_came_from(request))
    links.append(h.menu_item(_("Overview"), "booking_overview", **data))
    links.append(h.menu_item(_("Add"), "booking_add", **data))
    return [{"value": "Navigation", "children": links}]


def customer_validate(node, value):
    request = get_current_request()
    try:
        models.Customer.get_by(id=value, retailer=request.group)
    except sa_orm.exc.NoResultFound:
        raise colander.Invalid(node, "Invalid Customer")


def entities_validate(node, values):
    request = get_current_request()
    try:
        results = models.Entity.query.filter(
                models.Entity.id.in_(list(values)),
                models.Entity.retailer==request.group).all()
        assert len(results) == len(values)
    except sa_orm.exc.NoResultFound, AssertionError:
        raise colander.Invalid(node, "Invalid entity")


def location_validate(node, value):
    request = get_current_request()
    try:
        models.Location.get_by(id=value, retailer=request.group)
    except sa_orm.exc.NoResultFound:
        raise colander.Invalid(node, "Invalid Location")


def populate_schema(request, schema):
    """
    Helper to populate the schema
    """
    entities = []
    for e in models.Entity.all_by(retailer=request.group):
        entities.append((e.id, e.name))
    schema["entities"].widget.values = entities

    schema["customer"].widget.values = [(c.id, c.name) \
            for c in models.Customer.all_by(retailer=request.group)]

    locations = models.Location.all_by(retailer=request.group)
    location_data = [(l.id, l.name) for l in locations]
    schema["start_location"].widget.values = location_data
    schema["end_location"].widget.values = location_data
    return schema


def pre_save(form_obj, appstruct):
    appstruct["entities"] = [{"id": i} for i in appstruct["entities"]]

    for key in ["customer", "start_location", "end_location"]:
        appstruct[key + "_id"] = appstruct.pop(key)
    return appstruct


class Entities(colander.SequenceSchema):
    entity = colander.SchemaNode(colander.String())


class BookingSchema(colander.Schema):
    """
    A Schema for a booking
    """
    entities = Entities(
        validator=entities_validate,
        title=_("Entity to book"),
        widget=db_widget.ChosenMultipleWidget())
    customer = colander.SchemaNode(
        colander.String(),
        validator=customer_validate,
        title=_("Customer"),
        widget=db_widget.ChosenSingleWidget())
    price = colander.SchemaNode(
        colander.Int(),
        title=_("Price"))
    start_location = colander.SchemaNode(
        colander.String(),
        validator=location_validate,
        title=_("Start location"),
        widget=db_widget.ChosenSingleWidget())
    start_at = colander.SchemaNode(
        colander.DateTime(None),
        title=_("Starts At"))
    end_location = colander.SchemaNode(
        colander.String(),
        validator=location_validate,
        title=_("End location"),
        widget=db_widget.ChosenSingleWidget())
    end_at = colander.SchemaNode(
        colander.DateTime(None),
        title=_("Ends time"))


class BookingAddForm(h.AddFormView):
    item_type = _(u"Booking")
    buttons = (deform.Button("add_booking", _("Add Booking")),
                deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = BookingSchema()
        populate_schema(self.request, schema)
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("booking_overview",
                **h.get_nav_data(self.request))

    def add_booking_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        pre_save(self, appstruct)
        obj = models.Booking().from_dict(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = self.request.route_url(
            "booking_overview", **h.get_nav_data(self.request))
        return HTTPFound(location=location)



class BookingForm(h.EditFormView):
    def schema_factory(self):
        schema = BookingSchema()
        populate_schema(self.request, schema)
        return schema

    def before(self, form):
        appstruct = self.context.to_dict()
        appstruct["entities"] = [e.id for e in self.context.entities]
        form.appstruct = appstruct

    @property
    def cancel_url(self):
        return self.request.route_url("booking_overview",
                **h.get_nav_data(self.request))
    success_url = cancel_url

    def save_success(self, appstruct):
        pre_save(self, appstruct)
        return super(BookingForm, self).save_success(appstruct)


@view_config(route_name="booking_add", permission="view",
            renderer="add.mako")
def booking_add(context, request):
    return h.mk_form(BookingAddForm, context, request,
        extra={"sidebar_data": booking_links(request)})


@view_config(route_name="booking_manage", permission="view",
            renderer="booking_manage.mako")
def booking_manage(context, request):
    obj = models.Booking.get_by(id=request.matchdict["id"])

    form = h.mk_form(BookingForm, obj, request)
    if request.is_response(form):
        return form

    return {
        "sidebar_data": booking_actions(request),
        "form": form}


@view_config(route_name="booking_overview", permission="view",
            renderer="booking_overview.mako")
def booking_overview(context, request):
    deleted = request.params.get("deleted", False)

    search_opts = search.search_options(request)
    search_opts["filter_by"]["retailer"] = request.group
    q = models.Booking.query.options(
            sa_orm.joinedload("customer"),
            sa_orm.joinedload("entities"))
    bookings = models.Booking.search(query=q, **search_opts)

    columns = ["id", "entities_count"] + models.Booking.exposed_attrs()
    grid = h.PyramidGrid(bookings, columns, request=request,
            url=request.current_route_url)

    grid.exclude_ordering = ("id", "customer", "start_location", "end_location",
            "entities_count")
    grid.labels["id"] = ""

    grid.column_formats["id"] = lambda cn, i, item: h.column_link(
        request, "Manage", "booking_manage", url_kw=item.to_dict(),
        class_="btn btn-primary")

    return {
        "sidebar_data": booking_links(request),
        "booking_grid": grid}


def includeme(config):
    config.add_route("booking_add", "/g,{group}/booking/add")
    config.add_route("booking_manage", "/g,{group}/booking/{id}")
    config.add_route("booking_overview", "/g,{group}/booking")
