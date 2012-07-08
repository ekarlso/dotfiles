import logging

import colander
import deform
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, SequenceWidget
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.view import view_config

from .. import models, security
from ..utils import _
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import menu_item, get_url


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
    pk = _pk(appstruct)
    # NOTE: user_permissions or permissions
    appstruct[pk] = [{"perm_name": pn} for pn in appstruct.pop(pk)]
    return appstruct


def tenant_from_request(request):
    if "group_id" in request.GET:
        tenant = request.GET["group_id"]
    elif "group_name" in request.GET:
        tenant = request.GET["group_name"]
    else:
        tenant = None
    return tenant


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
        #location = self.request.url.split('?')[0] + '?' + urlencode(
        #    {'extra': name})
        user = models.User().from_dict(appstruct).save()
        if appstruct.pop("send_email", False):
            security.email_set_password(user, self.request)
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
    """
    Users preferences
    """
    user = request.user
    return mk_form(UserForm, user, request,
        extra={"nav_data": prefs_menu()})


@view_config(route_name="user_tenant_setter", permission="view")
def user_tenant_setter(request):
    """
    Method to help change tenants / groups.

    It sets the tenant if a "name" is in the params list and forwards the user
    to that tenants dashboard
    """
    tenant = tenant_from_request(request)

    def redirect(group):
        location = request.route_url("retailer_dashboard", group=group)
        return HTTPFound(location=location)

    # NOTE: Check for tenant
    # * Check > update db with new tenant > forward
    # * No tenant > forward to current tenant or default
    if tenant:
        # NOTE: Ok, so if there's a group and it's valid let's update in redis
        # and forward
        if request.user.has_group(tenant):
            request.user.current_group = tenant
            request.user.save()
            return redirect(tenant)
        else:
            raise HTTPForbidden
    else:
        tenant = request.group or request.user.current_group
        if tenant:
            return redirect(tenant)
        else:
            return HTTPFound(location=request.route_url("user_tenants"))


@view_config(route_name="user_tenants", permission="view",
        renderer="user_tenants_overview.mako")
def user_tenants(request):
    grid = PyramidGrid(request.user.retailers,
        ["group_name", "group_type"])
    return {"grid": grid}


def includeme(config):
    config.add_route("auth_settings", "@@admin/auth")
    # NOTE: Group links
    config.add_route("group_edit", "@@admin/group/{group_name}/edit")
    # NOTE: User links
    config.add_route("user_edit", "@@admin/user/{id}/edit")

    config.add_route("user_prefs", "@@prefs")
    config.add_route("user_tenant_setter", "@@tenant")
    config.add_route("user_tenants", "@@tenant/list")
