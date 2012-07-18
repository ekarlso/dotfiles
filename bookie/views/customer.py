import logging

import colander
import deform
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


"""
Manage Customers for Retailers
"""


def customer_actions(obj=None, request=None):
    data = get_nav_data(request)

    links = customer_links(obj, request)
    actions = []
    return links + actions


def customer_links(obj=None, request=None):
    data = get_nav_data(request)

    children = []
    children.append(menu_item(_("Overview"), "customer_overview", **data))
    return [{"value": "Navigation", "children": children}]


class CustomerSchema(colander.Schema):
    name = colander.SchemaNode(
        colander.String(),
        title=_("Name"))


class CustomerAddForm(AddFormView):
    item_type = _(u"Customer")
    buttons = (deform.Button("add_customer", _("Add Customer")),
                deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CustomerSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("customer_overview",
                **get_nav_data(self.request))

    def add_customer_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        # NOTE: Pass retailer for ownership :)
        obj = models.Customer(retailer=self.request.group).\
            update(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = self.cancel_url
        return HTTPFound(location=location)


class CustomerForm(EditFormView):
    def schema_factory(self):
        schema = CustomerSchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("customer_overview",
                **get_nav_data(self.request))
    success_url = cancel_url

    def save_success(self, appstruct):
        return super(CustomerForm, self).save_success(appstruct)


@view_config(route_name="customer_add", permission="view", renderer="add.mako")
def customer_add(context, request):
    return mk_form(CustomerAddForm, context, request)


@view_config(route_name="customer_manage", permission="view", renderer="customer_manage.mako")
def customer_manage(context, request):
    obj = models.Customer.get_by(id=request.matchdict["id"], retailer=request.group)

    form = mk_form(CustomerForm, obj, request)
    if request.is_response(form):
        return form

    return {"sidebar_data": customer_actions(request=request), "form": form}


@view_config(route_name="customer_overview", permission="view",
        renderer="customer_overview.mako")
def customer_overview(context, request):
    customers = models.Customer.all_by(retailer=request.group)

    columns = models.Customer.exposed_attrs()
    grid = PyramidGrid(customers, columns, request=request, url=request.current_route_url)

    grid.exclude_ordering = ["id"]

    grid.column_formats["name"] = lambda cn, i, item: column_link(
        request, unicode(item), "customer_manage", url_kw=item.to_dict())


    return {"sidebar_data": customer_actions(request=request),
            "grid": grid}


def includeme(config):
    config.add_route("customer_add", "/g,{group}/customer/add")
    config.add_route("customer_manage", "/g,{group}/customer/{id}")
    config.add_route("customer_overview", "/g,{group}/customer")
