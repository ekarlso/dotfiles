import logging
import pdb

import colander
import deform
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.view import view_config

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from . import helpers as h, search
from .search import search_options



LOG = logging.getLogger(__name__)


def get_type(obj):
    """
    Get a type from a request

    :param obj: Get the type from this
    """
    return obj.matchdict["type"] if isinstance(obj, Request) else obj.type


def get_model(obj):
    """
    Get a sqla model based upon the type from the type in matchdict

    :param obj: Object from which to get the model via
    """
    t = get_type(obj)
    try:
        tm = getattr(models, name_to_camel(t))
    except AttributeError:
        raise HTTPNotFound(_("Invalid type ${type} requested",
            mapping=dict(type=t)))
    return tm


# TODO: Make these better?
def entity_actions(request, obj=None):
    """
    Entity actions - on a entity page
    """
    # NOTE: Needs to pass in "type" here since it's not a part of the matchdict
    data = h.get_nav_data(request)

    links = entity_links(request, obj)
    actions = []
    actions.append(h.menu_item(_("View"), "entity_view", **data))
    actions.append(h.menu_item(_("Edit"), "entity_manage", **data))
    actions.append(h.menu_item(_("Delete"), "entity_delete", **data))
    actions.append(h.menu_item(_("Book me"), "booking_add",
                _query=dict(came_from=request.url, entity=data["id"]), **data))
    links.append({"value": _("Actions"), "children": actions})
    return links


def entity_links(request, obj=None):
    """
    Return some navigation links
    """
    data = h.get_nav_data(request)

    links = []
    links.append(h.menu_came_from(request))
    links.append(h.menu_item(_("Overview"), "entity_overview", **data))
    links.append(h.menu_item(_("Add"), "entity_add", **data))
    links.append(h.menu_item(_("Bulk add"), "entity_bulk_add", **data))
    return [{"value": _("Navigation"), "children": links}]


class CarSchema(colander.Schema):
    brand = colander.SchemaNode(
        colander.String(),
        eitle=_("Car"))
    model = colander.SchemaNode(
        colander.String(),
        title=_("Model"))
    produced = colander.SchemaNode(
        colander.String(),
        title=_("Produced"))
    identifier = colander.SchemaNode(
        colander.String(),
        title=_("Identifier"))


class CarAddForm(h.AddFormView):
    item_type = u"Car"
    buttons = (deform.Button("add_car", _("Add Car")),
                deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CarSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("entity_overview",
                **get_nav_data(self.request))

    def add_car_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        car = models.Car(retailer=self.request.group).\
                update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=car.title)), "success")
        location = self.request.route_url("entity_view",
                id=car.id, **get_nav_data(self.request))
        return HTTPFound(location=location)


class Row(colander.TupleSchema):
    brand = colander.SchemaNode(colander.String())
    model = colander.SchemaNode(colander.String())
    produced = colander.SchemaNode(colander.Integer())
    identifier = colander.SchemaNode(colander.String())
    metadata = colander.SchemaNode(colander.String(), missing={})


class Rows(colander.SequenceSchema):
    row = Row()


class Schema(colander.Schema):
    csv = Rows(widget=deform.widget.TextAreaCSVWidget(rows=20, columns=100))


# TODO: Make it possible to choose / enter in Entity Type to load
class CarBulkForm(CarAddForm):
    buttons = (deform.Button("bulk_load", _("Bulk add")),
            deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        return Schema()

    def bulk_load_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        for row in appstruct["csv"]:
            # NOTE: First create new Entity
            name = "%s: %s - %s - %s" % row[:4]

            entity = models.Entity(
                    type="car", retailer=self.request.group, name=name)
            # NOTE: Then the metadata using x.set_meta
            meta_data = [pair.split("=") for pair in row[4].split(":")]
            for k, v in meta_data:
                models.EntityMetadata(name=k, value=v, entity=entity)
            entity.save()

        location = self.request.route_url("entity_overview",
                **get_nav_data(self.request))
        return HTTPFound(location=location)


class CarForm(h.EditFormView):
    def schema_factory(self):
        return CarSchema()

    @property
    def cancel_url(self):
        return self.request.route_url("entity_view",
                **get_nav_data(self.request))
    success_url = cancel_url

    def save_success(self, appstruct):
        return super(CarForm, self).save_success(appstruct)



@view_config(route_name="entity_add", permission="view",
        renderer="add.mako")
def entity_add(context, request):
    type_ = request.GET.get("type")

    return h.mk_form(CarAddForm, context, request,
            extra={"sidebar_data": entity_links(request), "page_title": _("Add")})


@view_config(route_name="entity_bulk_add", permission="view",
        renderer="add.mako")
def entity_bulk_add(context, request):
    form = h.mk_form(CarBulkForm, context, request,
            extra={"sidebar_data": entity_links(request),
                "page_title": _("Bulk add")})
    return form


@view_config(route_name="entity_manage", permission="view",
            renderer="edit.mako")
def entity_manage(context, request):
    obj = models.Entity.get_by(
            id=request.matchdict["id"],
            retailer=request.group)

    return h.mk_form(CarForm, obj, request,
        extra=dict(sidebar_data=entity_actions(request, obj)))


@view_config(route_name="entity_view", permission="view",
            renderer="entity_view.mako")
def entity_view(context, request):
    entity = models.Entity.get_by(
            id=request.matchdict["id"],
            retailer=request.group)

    ##b_latest = models.Booking.latest(entity=entity)
    b_grid_latest = h.PyramidGrid(
        models.Booking.latest(filter_by={"entity": entity}),
        models.Booking.exposed_attrs())

    return {
        "sidebar_data": entity_actions(request, entity),
        "sub_title": entity.title,
        "entity": entity,
        "b_grid_latest": b_grid_latest}


@view_config(route_name="entity_delete", permission="delete",
            renderer="delete.mako")
def entity_delete(context, request):
    entity = models.Entity.get_by(
            id=request.matchdict["id"],
            retailer=request.group).one()

    if request.params.get("do") == "yes":
        entity.delete()
        request.session.flash(_("Delete successful"))
        return HTTPFound(location=request.route_url(
            "entity_type_overview", type=entity.type))
    return {
        "sidebar_data": entity_actions(request, obj),
        "sub_title": entity.title}


@view_config(route_name="entity_overview", permission="view",
            renderer="entity_overview.mako")
def entity_overview(context, request):
    search_opts = search.search_options(request)
    search_opts["filter_by"]["retailer"] = request.group
    entities = models.Entity.search(**search_opts)

    columns = ["id"] + models.Entity.exposed_attrs()
    grid = h.PyramidGrid(entities, columns, request=request,
            url=request.current_route_url)

    grid.exclude_ordering = ["id", "color"]
    grid.labels["id"] = ""

    grid.column_formats["id"] = lambda cn, i, item: h.column_link(
        request, "Manage", "entity_view", url_kw=item.to_dict(),
        class_="btn btn-primary")

    return {
        "sidebar_data": entity_links(request),
        "entity_grid": grid}


def includeme(config):
    config.add_route("entity_add", "/g,{group}/entity/add")
    config.add_route("entity_bulk_add", "/g,{group}/entity/bulk_add")
    config.add_route("entity_manage", "/g,{group}/entity/{id}/manage")
    config.add_route("entity_view", "/g,{group}/entity/{id}/view")
    config.add_route("entity_delete", "/g,{group}/entity/{id}/delete")
    config.add_route("entity_overview", "/g,{group}/entity")
