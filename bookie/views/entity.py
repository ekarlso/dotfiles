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
from .helpers import menu_item, menu_came_from, get_nav_data



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
    data = get_nav_data(request)

    links = entity_links(request, obj)
    actions = []
    actions.append(menu_item(_("View"), "entity_view", **data))
    actions.append(menu_item(_("Edit"), "entity_edit", **data))
    actions.append(menu_item(_("Delete"), "entity_delete", **data))
    actions.append(menu_item(_("Book me"), "booking_add",
                _query=dict(came_from=request.url, entity=data["id"]), **data))
    links.append({"value": _("Actions"), "children": actions})
    return links


def entity_links(request, obj=None):
    """
    Return some navigation links
    """
    data = get_nav_data(request)

    links = []
    links.append(menu_came_from(request))
    links.append(menu_item(_("Overview"), "entity_overview", **data))
    links.append(menu_item(_("Add"), "entity_add", **data))
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


class CarAddForm(AddFormView):
    item_type = u"Car"
    buttons = (Button("add_car", _("Add Car")),
                Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CarSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("entity_overview",
                **get_nav_data(self.request))

    def add_car_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        car = models.Car(retailer=request.group).\
                update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=car.title)), "success")
        location = request.route_url("entity_view"
                **get_nav_data(self.request))
        return HTTPFound(location=location)



class CarForm(EditFormView):
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

    return mk_form(CarAddForm, context, request,
            extra={"sidebar_data": entity_links(request), "page_title": _("Add")})


@view_config(route_name="entity_edit", permission="view",
            renderer="edit.mako")
def entity_edit(context, request):
    obj = models.Entity.query.filter_by(
        id=request.matchdict["id"], retailer=request.group).one()
    return mk_form(CarForm, obj, request,
        extra=dict(sidebar_data=entity_actions(request, obj)))


@view_config(route_name="entity_view", permission="view",
            renderer="entity_view.mako")
def entity_view(context, request):
    deleted = request.params.get("deleted", False)
    entity = models.Entity.query.filter_by(
        deleted=deleted, id=request.matchdict["id"]).one()

    ##b_latest = models.Booking.latest(entity=entity)
    b_grid_latest = PyramidGrid(
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
    entity = models.Entity.query.filter_by(
        deleted=False, id=request.matchdict["id"]).one()
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
    deleted = request.params.get("deleted", False)

    filter_by = dict(
            retailer=request.group)
    entities = models.Entity.search(filter_by=filter_by)

    columns = ["id"] + models.Entity.exposed_attrs()
    grid = PyramidGrid(entities, columns, request=request,
            url=request.current_route_url)

    grid.exclude_ordering = ["id"]
    grid.labels["id"] = ""

    grid.column_formats["id"] = lambda cn, i, item: column_link(
        request, "Manage", "entity_view", url_kw=item.to_dict(),
        class_="btn btn-primary")

    return {
        "sidebar_data": entity_links(request),
        "entity_grid": grid}


def includeme(config):
    config.add_route("entity_add", "/g,{group}/entity/add")
    config.add_route("entity_edit", "/g,{group}/entity/{id}/edit")
    config.add_route("entity_view", "/g,{group}/entity/{id}/view")
    config.add_route("entity_delete", "/g,{group}/entity/{id}/delete")
    config.add_route("entity_overview", "/g,{group}/entity")
