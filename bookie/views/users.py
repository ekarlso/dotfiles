from pprint import pformat
import logging
import re
from urllib import urlencode

import colander
import deform
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, CheckboxChoiceWidget, PasswordWidget, SequenceWidget
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import Forbidden
from pyramid.view import view_config

from .. import models
from ..utils import _
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import menu_item


LOG = logging.getLogger(__name__)


def roleset_validator(node, value):
    """
    Validate roles
    """
    oneof = colander.OneOf(models.permission_names())
    [oneof(node, item) for item in value]


def group_validator(node, value):
    """
    Validate a group
    """
    group = models.Group.by_group_name(value)
    if not group:
        raise colander.Invalid(node, _(u"No such group: ${group}",
                                mapping=dict(group=value)))

def _pk(data):
    """
    Get a permission key
    """
    return "user_permissions" if "first_name" in data else "permissions"


def _all_from_db(schema):
    """
    Get's all the available roles / groups and adds them to the schema
    """
    if "groups" in schema:
        schema["groups"]["group"].widget.values = \
            [dict(label=g.group_name, value=g.group_name) \
                for g in models.Group.query.all()]
    schema[_pk(schema)].widget.values = models.permission_pairs()
    return schema


def _mangle_appstruct(appstruct):
    """
    Helper to convert data from dict data to SA data
    """
    if "groups" in appstruct:
        # NOTE: Should probably do the Group ID here from the form instead of
        #       looking up the name
        appstruct["groups"] = [{"group_name": models.Group.by_group_name(g).\
            group_name}for g in appstruct.pop("groups")]

    # NOTE: Mangle permissions
    pk = _pk(appstruct) # NOTE: user_permissions or permissions
    appstruct[pk] = [{"perm_name": pn} for pn in appstruct.pop(pk)]
    return appstruct


def prefs_menu():
    return [{
        "value": _("My settings"), "children": [
            menu_item(_("Preferences"), "user_prefs"),
            menu_item(_("Reset password"), "reset_password")]}]


class Groups(colander.SequenceSchema):
    group = colander.SchemaNode(
        colander.String(),
        title=_(u'Group'),
        validator=group_validator,
        missing=None,
        widget=AutocompleteInputWidget())


class UserSimpleSchema(colander.Schema):
    user_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Username"))
    first_name = colander.SchemaNode(
        colander.String(),
        title=_(u"First Name"))
    middle_name = colander.SchemaNode(
        colander.String(),
        missing='',
        title=_(u"Middle Name"))
    last_name = colander.SchemaNode(
        colander.String(),
        title=_(u"Last Name"))
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=CheckedPasswordWidget(length="20"),
        title=_(u"Password"),
        description=_(u"Enter password..."))
    email = colander.SchemaNode(
        colander.String(),
        title=_(u"E-Mail"))
    status = colander.SchemaNode(
        colander.Boolean(),
        title=_(u'Active'),
        description=_(u"Untick this to deactivate the account."))


class UserSchema(UserSimpleSchema):
    groups = Groups(
        title=_(u'Groups'),
        missing=[],
        widget=SequenceWidget(min_len=1))
    user_permissions = colander.SchemaNode(
        deform.Set(allow_empty=True),
        validator=roleset_validator,
        missing=[],
        title=_(u"Permissions"),
        widget=CheckboxChoiceWidget())


class GroupSchema(colander.Schema):
    group_name = colander.SchemaNode(colander.String(), title=_(u'Group name'))
    permissions = colander.SchemaNode(
        deform.Set(allow_empty=True),
        validator=roleset_validator,
        missing=[],
        title=_(u"Permissions"),
        widget=CheckboxChoiceWidget())


class UserAddForm(AddFormView):
    item_type = _(u'User')
    buttons = (Button('add_user', _(u'Add User')),
               Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = UserSchema()
        _all_from_db(schema)
        schema.add(colander.SchemaNode(
            colander.Boolean(),
            name=u'send_email',
            title=_(u'Send password registration link'),
            default=True,))
        return schema

    def add_user_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        _mangle_appstruct(appstruct)
        appstruct['email'] = appstruct['email'] and appstruct['email'].lower()
        if appstruct.pop("send_email", False):
            security.email_set_password(get_principals()[name], self.request)
        #location = self.request.url.split('?')[0] + '?' + urlencode(
        #    {'extra': name})
        user = models.User().from_dict(appstruct).save()
        self.request.session.flash(_(u'${title} added.',
                                     mapping=dict(title=user.title)),
                                     'success')
        return HTTPFound(location=get_url("auth_settings"))


class GroupAddForm(AddFormView):
    item_type = _(u'Group')
    buttons = (Button('add_group', _(u'Add Group')),
               Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = GroupSchema()
        _all_from_db(schema)
        return schema

    def add_group_success(self, appstruct):
        _mangle_appstruct(appstruct)
        models.Group().from_dict(appstruct).save()
        return HTTPFound(location=get_url("auth_settings"))


class UserForm(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return UserSimpleSchema()


class UserEditForm(UserForm):
    def before(self, form):
        d = self.context.to_dict()
        # NOTE: A User has groups. Load them
        if "groups" in self.schema:
            d["groups"] = self.context.groups
        # NOTE: Get permissions
        d[_pk(d)] = [p.perm_name for p in self.context[_pk(d)]]
        form.appstruct = d

    def schema_factory(self):
        s = UserSchema()
        _all_from_db(s)
        del s["password"]
        return s

    @property
    def cancel_url(self):
        return get_url("auth_settings")

    def save_success(self, appstruct):
        _mangle_appstruct(appstruct)
        return super(UserForm, self).save_success(appstruct)


class GroupEditForm(UserEditForm):
    def schema_factory(self):
        s = GroupSchema()
        _all_from_db(s)
        return s


@view_config(route_name="auth_settings", permission="system.admin",
            renderer="admin/auth_settings.mako")
def auth_settings(context, request):
    users = models.User.query.all()
    user_grid = PyramidGrid(users, ["title", "email"])

    groups = models.Group.query.all()
    group_grid = PyramidGrid(groups, models.Group.exposed_attrs())

    user_addform = UserAddForm(context, request)()
    if request.is_response(user_addform):
        return user_addform

    group_addform = GroupAddForm(context, request)()
    if request.is_response(group_addform):
        return group_addform

    return {
        "user_grid": user_grid,
        "user_addform": user_addform,
        "group_grid": group_grid,
        "group_addform": group_addform}


@view_config(route_name="group_edit", permission="system.admin",
            renderer="edit.mako")
def group_edit(request):
    group = models.Group.query.filter_by(
        group_name=request.matchdict["group_name"]).one()
    return mk_form(GroupEditForm, group, request)


@view_config(route_name="user_edit", permission="system.admin",
            renderer="edit.mako")
def user_edit(request):
    user = models.User.query.filter_by(id=request.matchdict["id"]).one()
    return mk_form(UserEditForm, user, request)


@view_config(route_name="user_prefs", permission="view",
            renderer="user_prefs.mako")
def user_preferences(request):
    user = request.user
    return mk_form(UserForm, user, request,
        extra={"navtree": prefs_menu()})


def includeme(config):
    config.add_route("auth_settings", "@@admin/auth")
    # NOTE: Group links
    config.add_route("group_edit", "@@admin/group/{group_name}/edit")
    # NOTE: User links
    config.add_route("user_prefs", "@@prefs")
    config.add_route("user_edit", "@@admin/user/{id}/edit")
