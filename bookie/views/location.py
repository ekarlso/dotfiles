import logging

import colander
import deform
import pyramid.httpexceptions as exceptions
from pyramid.request import Request
from pyramid.view import view_config
from sqlalchemy.orm import exc

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from . import helpers as h, search


def get_actions(request, obj=None):
    data = h.get_nav_data(request)

    links = get_links(request, obj=obj)
    actions = []
    actions.append({"value": _("Manage"), "route": "location_manage",
        "url_kw": data})
    links.append({"value": _("Actions"), "children": actions})
    return links


def get_links(request, obj=None):
    data = h.get_nav_data(request)

    links = []
    links.append(h.menu_item(_("Overview"), "location_overview", **data))
    links.append(h.menu_item(_("Add"), "location_add", **data))
    links.append(h.menu_came_from(request))
    return [{"value": _("Navigation"), "children": links}]


class LocationSchema(colander.Schema):
    address = colander.SchemaNode(
        colander.String())
    city = colander.SchemaNode(
        colander.String())
    postal_code = colander.SchemaNode(
        colander.Integer())


class LocationAddForm(h.AddFormView):
    item_type = u"Location"
    buttons = (deform.Button("add_location", _("Add") + " " + _("Location")),
                deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = LocationSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("entity_overview",
                **h.get_nav_data(self.request))

    def add_location_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        obj = models.Location(retailer=self.request.group).\
                update(appstruct).save()
        self.request.session.flash(_(u"${name} added.",
            mapping=dict(name=obj.name)), "success")
        location = self.request.route_url("location_overview",
                id=obj.id, **h.get_nav_data(self.request))
        return exceptions.HTTPFound(location=location)


@view_config(route_name="location_add", renderer="add.mako")
def location_add(context, request):
    extra = {
            "sidebar_data": get_links(request),}
    return h.mk_form(LocationAddForm, context, request, extra=extra)


class LocationForm(h.EditFormView):
    def schema_factory(self):
        return LocationSchema()

    @property
    def cancel_url(self):
        return self.request.route_url("location_manage",
                **h.get_nav_data(self.request))
    success_url = cancel_url

    def save_success(self, appstruct):
        return super(LocationForm, self).save_success(appstruct)


@view_config(route_name="location_manage", permission="view",
        renderer="location_manage.mako")
def location_manage(context, request):
    obj = models.Location.get_by(
            id=request.matchdict["id"],
            retailer=request.group)

    form = h.mk_form(LocationForm, obj, request)
    if request.is_response(form):
        return form

    return {"sidebar_data": get_actions(request), "form": form}


@view_config(route_name="location_overview", renderer="grid.mako")
def location_overview(context, request):
    search_opts = search.search_options(request)
    search_opts["filter_by"]["retailer"] = request.group
    objects = models.Location.search(**search_opts)

    columns = ["id"] + models.Location.exposed_attrs()
    grid = h.PyramidGrid(objects, columns, request=request,
            url=request.current_route_url)

    grid.exclude_ordering = ["id"]
    grid.labels["id"] = ""

    grid.column_formats["id"] = lambda cn, i, item: h.column_link(
            request, "Manage", "location_manage", url_kw=item.to_dict(),
            class_="btn btn-primary")

    return {
            "sidebar_data": get_links(request),
            "grid": grid}


def includeme(config):
    config.add_route("location_add", "/g,{group}/location/add")
    config.add_route("location_manage", "/g,{group}/location/{id}")
    config.add_route("location_overview", "/g,{group}/location")
