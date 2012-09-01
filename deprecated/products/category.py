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

from bookie.models import models
from bookie.utils import _
from .. import helpers as h, search
from . import get_links


LOG = logging.getLogger(__name__)


# TODO: Make these better?
def get_actions(request, obj=None):
    """
    Category actions - on a category page
    """
    # NOTE: Needs to pass in "type" here since it's not a part of the matchdict
    d = h.get_nav_data(request)

    actions = []
    actions.append(h.menu_item(_("Edit"), "category_manage", **d))

    links = get_links(request, obj)
    links.append({"value": _("Actions"), "children": actions})
    return links


class CategorySchema(colander.Schema):
    resource_name = colander.SchemaNode(
        colander.String(),
        title=_("Name"))
    description = colander.SchemaNode(
        colander.String(),
        missing=None,
        title=_("Description"))


class CategoryAddForm(h.AddFormView):
    item_type = u"Category"
    buttons = (Button("add_category", _("Add Category")),
                Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CategorySchema()
        return schema

    @property
    def cancel_url(self):
        return self.request.route_url("category_overview",
                **h.get_nav_data(self.request))

    def add_category_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        obj = models.Category(owner_group_id=self.request.account.id).\
                from_dict(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = self.request.route_url("category_overview",
                **h.get_nav_data(self.request))
        return HTTPFound(location=location)


class CategoryEditForm(h.EditFormView):
    @property
    def success_url(self):
        return self.request.url
    cancel_url = success_url

    def schema_factory(self):
        return CategorySchema()


@view_config(route_name="category_add", permission="view",
        renderer="add.mako")
def category_add(context, request):

    return h.mk_form(CategoryAddForm, context, request,
            extra={"sidebar_data": get_links(request), "page_title": _("Add")})


@view_config(route_name="category_manage", permission="view",
            renderer="edit.mako")
def category_manage(context, request):
    obj = models.Resource.query.filter_by(
        deleted=False, resource_id=request.matchdict["resource_id"]).one()
    return h.mk_form(CategoryEditForm, obj, request,
            extra={"sidebar_data": get_actions(request, obj)})


@view_config(route_name="category_overview", permission="view",
            renderer="category_overview.mako")
def category_overview(context, request):
    deleted = request.params.get("deleted", False)
    objects = models.Category.query.filter_by(deleted=deleted).\
        filter(models.Resource.owner_group_id==request.account.id).all()

    columns = models.Category.exposed_attrs()
    grid = h.PyramidGrid(objects, columns)

    grid.column_formats["resource_name"] = lambda cn, i, item: \
        h.column_link(request, item["resource_name"], "category_manage",
                url_kw=item.to_dict())

    return {
        "sidebar_data": get_links(request),
        "sub_title": _("Category management"),
        "grid": grid}
