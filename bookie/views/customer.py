import logging

import colander
import deform
from pyramid.httpexceptions import HTTPFound, HTTPNotFound
from pyramid.exceptions import Forbidden
from pyramid.request import Request
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config
from sqlalchemy.orm import exc

from .. import models
from ..utils import _, camel_to_name, name_to_camel
from . import helpers as h, search


LOG = logging.getLogger(__name__)


"""
Manage Customers for Retailers
"""


def customer_actions(request, obj=None):
    data = h.get_nav_data(request)

    links = customer_links(request, obj)
    actions = []
    actions.append(h.menu_item(_("Manage"), "customer_manage", **data))
    return links + [{"value": _("Actions"), "children": actions}]


def customer_links(request, obj=None):
    data = h.get_nav_data(request)

    links = []
    links.append(h.menu_came_from(request))
    links.append(h.menu_item(_("Overview"), "customer_overview", **data))
    links.append(h.menu_item(_("Add"), "customer_add", **data))
    return [{"value": _("Navigation"), "children": links}]


class CustomerSchema(colander.Schema):
    name = colander.SchemaNode(
        colander.String(),
        title=_("Name"))
    organization_id = colander.SchemaNode(
        colander.String(),
        title=_("Organization ID"))
    contact = colander.SchemaNode(
        colander.String(),
        title=_("Contact"))
    email = colander.SchemaNode(
        colander.String(),
        title=_("E-Mail"))
    phone = colander.SchemaNode(
        colander.String(),
        title=_("Phone"))


class CustomerAddForm(h.AddFormView):
    item_type = _(u"Customer")
    buttons = (deform.Button("add_customer", _("Add Customer")),
                deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CustomerSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("customer_overview",
                **h.get_nav_data(self.request))

    def add_customer_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        obj = models.Customer(retailer=self.request.group).\
            update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = self.cancel_url
        return HTTPFound(location=location)


class CustomerForm(h.EditFormView):
    def schema_factory(self):
        schema = CustomerSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("customer_overview",
                **h.get_nav_data(self.request))
    success_url = cancel_url

    def save_success(self, appstruct):
        return super(CustomerForm, self).save_success(appstruct)


@view_config(route_name="customer_add", permission="view",
        renderer="add.mako")
def customer_add(context, request):
    return h.mk_form(CustomerAddForm, context, request,
            extra={"sidebar_data": customer_links(request)})


@view_config(route_name="customer_manage", permission="view", renderer="customer_manage.mako")
def customer_manage(context, request):
    obj = models.Customer.get_by(id=request.matchdict["id"], retailer=request.group)

    form = h.mk_form(CustomerForm, obj, request)
    if request.is_response(form):
        return form

    return {"sidebar_data": customer_actions(request),"form": form}


@view_config(route_name="customer_overview", permission="view",
        renderer="customer_overview.mako")
def customer_overview(context, request):

    search_opts = search.search_options(request)
    search_opts["filter_by"]["retailer"] = request.group
    customers = models.Customer.search(**search_opts)

    columns = ["id"] + models.Customer.exposed_attrs()
    grid = h.PyramidGrid(customers, columns, request=request,
            url=request.current_route_url)

    grid.exclude_ordering = ["id"]
    grid.labels["id"] = ""

    grid.column_formats["id"] = lambda cn, i, item: h.column_link(
        request, "Manage", "customer_manage", url_kw=item.to_dict(),
        class_="btn btn-primary")

    return {"sidebar_data": customer_links(request),
            "grid": grid}


def includeme(config):
    config.add_route("customer_add", "/g,{group}/customer/add")
    config.add_route("customer_manage", "/g,{group}/customer/{id}")
    config.add_route("customer_overview", "/g,{group}/customer")
