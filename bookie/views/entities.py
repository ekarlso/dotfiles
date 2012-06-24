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
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import menu_item, get_url, create_anchor, wrap_td


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
def entity_actions(obj=None, request=None):
    return entity_links(obj) + [
        {"title": _("Entity Actions"), "children": [
            menu_item(_("View"), "entity_view", id=obj.id),
            menu_item(_("Edit"), "entity_edit", id=obj.id),
            menu_item(_("Delete"), "entity_delete", id=obj.id),
            menu_item(_("Book me"), "booking_add",
                    _query=dict(came_from=request.url))]}
        ]

def entity_links(obj=None):
    return [
        {"title": _("Navigation"), "children": [
            menu_item(_("Overview"), "entities_view", type=get_type(obj))]}]


class CarSchema(colander.Schema):
    brand = colander.SchemaNode(
        colander.String(),
        title=_("Car"))
    model = colander.SchemaNode(
        colander.String(),
        title=_("Model"))
    produced = colander.SchemaNode(
        colander.String(),
        title=_("Produced"))
    identifier = colander.SchemaNode(
        colander.String(),
        title=_("Identifier"))


class CarAddForm(AddFormView):
    item_type = u"Car"
    buttons = (Button("add_car", _("Add Car")),
                Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CarSchema()
        return schema

    def add_car_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        car = models.Car().update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=car.title)), "success")
        location = get_url("entities_view", type=self.item_type.lower())
        return HTTPFound(location=location)


class CarEditForm(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return CarSchema()


@view_config(route_name="entity_add", permission="add",
        renderer="add.mako")
def entity_add(context, request):
    type_ = get_type(request)
    return mk_form(CarAddForm, context, request,
        extra={"page_title": _("Add"), "sub_title": type_.title()})


@view_config(route_name="entity_edit", permission="edit",
            renderer="edit.mako")
def entity_edit(context, request):
    obj = models.Entity.query.filter_by(
        deleted=False, id=request.matchdict["id"]).one()
    return mk_form(CarEditForm, obj, request,
        extra=dict(navtree=entity_actions(obj=obj, request=request)))


@view_config(route_name="entity_view", permission="view",
            renderer="entity_view.mako")
def entity_view(context, request):
    deleted = request.params.get("deleted", False)
    entity = models.Entity.query.filter_by(
        deleted=deleted, id=request.matchdict["id"]).one()

    ##b_latest = models.Booking.latest(entity=entity)
    b_grid_latest = PyramidGrid(
        models.Booking.latest(filter_by=dict(entity=entity)),
        models.Booking.exposed_attrs())

    return {
        "navtree": entity_actions(entity, request),
        "entity": entity,
        "sub_title": entity.title,
        "b_grid_latest": b_grid_latest}


@view_config(route_name="entity_delete", permission="delete",
            renderer="delete.mako")
def entity_delete(context, request):
    entity = models.Entity.query.filter_by(
        deleted=False, id=request.matchdict["id"]).one()
    if request.params.get("do") == "yes":
        entity.delete()
        request.session.flash(_("Delete successful"))
        return HTTPFound(location=get_url("entities_view", type=entity.type))
    return {"navtree": entity_actions(entity, request),
        "sub_title": entity.title}


@view_config(route_name="entities_view", permission="view",
            renderer="entity_overview.mako")
def entities_view(context, request):
    deleted = request.params.get("deleted", False)
    type_ = get_type(request)
    type_model = get_model(request)

    entities = type_model.query.filter_by(deleted=deleted).all()

    grid = PyramidGrid(entities, type_model.exposed_attrs())
    grid.column_formats["brand"] = lambda cn, i, item: wrap_td(
        create_anchor(item["title"], "entity_view", type=type_, id=item["id"]))

    return {"navtree": entity_links(request),
        "entity_grid": grid, "sub_title": name_to_camel(type_, joiner=" ")}


def includeme(config):
    config.add_route("entity_add", "/entity/{type}/add")
    config.add_route("entity_edit", "/entity/{id}/edit")
    config.add_route("entity_view", "/entity/{id}/view")
    config.add_route("entity_delete", "/entity/{id}/delete")
    config.add_route("entities_view", "/entity/{type}")
