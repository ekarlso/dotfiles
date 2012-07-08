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
from .helpers import menu_item, get_nav_data, get_url, create_anchor


LOG = logging.getLogger(__name__)


# TODO: Make these better?
def category_actions(obj, request):
    """
    Category actions - on a category page
    """
    # NOTE: Needs to pass in "type" here since it's not a part of the matchdict
    d = get_nav_data(request, extra={})

    links = category_links(d)
    actions = []
    actions.append(menu_item(_("View"), "category_view", **d))
    actions.append(menu_item(_("Edit"), "category_edit", **d))
    actions.append(menu_item(_("Delete"), "category_delete", **d))
    links.append({"value": _("Category Actions"), "children": actions})
    return links


def category_links(data):
    """
    Return some navigation links
    """
    children = []
    children.append(menu_item(_("Overview"), "category_overview", **data))
    return [{"value": _("Navigation"), "children": children}]


class CategorySchema(colander.Schema):
    resource_name = colander.SchemaNode(
        colander.String(),
        title=_("Name"))
    description = colander.SchemaNode(
        colander.String(),
        missing=None,
        title=_("Description"))


class CategoryAddForm(AddFormView):
    item_type = u"Category"
    buttons = (Button("add_category", _("Add Category")),
                Button("cancel", _("Cancel")))

    def schema_factory(self):
        schema = CategorySchema()
        return schema

    def add_category_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        obj = models.Category().from_dict(appstruct).save()
        self.request.session.flash(_(u"${title} added.",
            mapping=dict(title=obj.title)), "success")
        location = get_url("category_overview")
        return HTTPFound(location=location)


class CategoryEditForm(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return CategorySchema()


@view_config(route_name="category_add", permission="add",
        renderer="add.mako")
def category_add(context, request):
    return mk_form(CategoryAddForm, context, request,
        extra={"page_title": _("Add")})


@view_config(route_name="category_edit", permission="edit",
            renderer="edit.mako")
def category_edit(context, request):
    obj = models.Resource.query.filter_by(
        deleted=False, resource_id=request.matchdict["resource_id"]).one()
    return mk_form(CategoryEditForm, obj, request,
        extra=dict(nav_data=category_actions(obj, request)))


@view_config(route_name="category_view", permission="view",
            renderer="category_view.mako")
def category_view(context, request):
    deleted = request.params.get("deleted", False)
    obj = models.Resource.get_by(
        deleted=deleted,
        resource_id=request.matchdict["resource_id"])
    return {
        "nav_data": category_actions(obj, request),
        "sub_title": obj.title,
        "obj": obj}


@view_config(route_name="category_delete", permission="delete",
            renderer="delete.mako")
def category_delete(context, request):
    obj = models.Category.query.filter_by(
        deleted=False, resource_id=request.matchdict["resource_id"]).one()
    if request.params.get("do") == "yes":
        obj.delete()
        request.session.flash(_("Delete successful"))
        return HTTPFound(location=get_url("category_overview"))
    return {
        "nav_data": category_actions(obj, request),
        "sub_title": obj.title}


@view_config(route_name="category_overview", permission="view",
            renderer="category_overview.mako")
def category_overview(context, request):
    deleted = request.params.get("deleted", False)
    objects = models.Category.query.filter_by(deleted=deleted).\
        filter(models.Resource.owner_group_name==request.group).all()

    grid = PyramidGrid(objects, models.Category.exposed_attrs())
    grid.column_formats["resource_name"] = lambda cn, i, item: \
        column_link(request, item["resource_name"], "category_view", view_kw=item.to_dict())

    return {
        "nav_data": category_links(get_nav_data(request)),
        "sub_title": _("Category management"),
        "grid": grid}


def includeme(config):
    config.add_route("category_add", "/@{group}/category/add")
    config.add_route("category_edit", "/@{group}/category/{resource_id}/edit")
    config.add_route("category_view", "/@{group}/category/{resource_id}/view")
    config.add_route("category_delete", "/@{group}/category/{resource_id}/delete")
    config.add_route("category_overview", "/@{group}/category")
