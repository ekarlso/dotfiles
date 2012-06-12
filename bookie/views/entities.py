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
from .helpers import get_url, create_anchor, wrap_td


LOG = logging.getLogger(__name__)


from colanderalchemy import SQLAlchemyMapping



def get_type(obj):
    """
    Get a type from a request

    :param obj: Get the type from this
    """
    return obj.matchdict["type"] if isinstance(obj, Request) else obj


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
        #schema = models.Car.get_schema()
        schema = SQLAlchemyMapping(models.Entity)
        #print "SCHEMA IS", schema
        return schema

    def add_car_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        car = models.Car().update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=car.title)), "success")
        location = get_url("entities_manage", type=self.item_type.lower())
        return HTTPFound(location=location)


class CarEditForm(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return CarSchema()


@view_config(route_name="entity_add", renderer="bookie:templates/entity/add.pt")
def entity_add(context, request):
    type_ = get_type(request)
    s = models.Car.get_schema()
    return mk_form(CarAddForm, context, request)


@view_config(route_name="entity_manage",
            renderer="bookie:templates/entity/edit.pt")
def entity_manage(context, request):
    type_ = get_type(request)
    obj = get_model(request).query.filter_by(id=request.matchdict["id"]).one()
    return mk_form(CarEditForm, obj, request)


@view_config(route_name="entities_manage", renderer="bookie:templates/entity/list.pt")
def entities_manage(context, request):
    type_ = get_type(request)
    type_model = get_model(type_)

    entities = type_model.query.all()
    grid = PyramidGrid(entities, type_model.exposed_columns())
    grid.column_formats["brand"] = lambda col_num, i, item: \
        wrap_td(
            create_anchor(
                item["title"], "entity_manage", type=type_, id=1))
    return {"entity_grid": grid, "entity_type": camel_to_name(type_)}


def includeme(config):
    config.add_route("entity_add", "/entity/{type}/add")
    config.add_route("entities_manage", "/entity/{type}")
    config.add_route("entity_manage", "/entity/{type}/{id}")
