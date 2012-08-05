import logging

import colander
import deform
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, SequenceWidget
from pyramid.httpexceptions import HTTPFound, HTTPNotFound, HTTPForbidden
from pyramid.view import view_config

from .. import models, security
from ..utils import _
from . import helpers as h, search


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


def group_from_request(request):
    if "id" in request.GET:
        group = request.GET["id"]
    else:
        group = None
    return group


def prefs_menu():
    links = []
    links.append({"value": _("Preferences"), "route": "user_account"})
    #links.append({"value": _("Reset Password"), "route": "reset_password"})
    return [{"value": _("My settings"), "children": links}]


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


class UserAddForm(h.AddFormView):
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
        return HTTPFound(location=self.request.route_url("principal_manage"))


class GroupAddForm(h.AddFormView):
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
        return HTTPFound(location=self.request.route_url("principals_manage"))


class UserForm(h.EditFormView):
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
        return self.request.route_url("principals_manage")

    def save_success(self, appstruct):
        _mangle_appstruct(appstruct)
        return super(UserForm, self).save_success(appstruct)


class GroupEditForm(UserEditForm):
    def schema_factory(self):
        s = GroupSchema()
        _all_from_db(s)
        return s


@view_config(route_name="principals_manage", permission="admin",
            renderer="admin/principals.mako")
def principals_manage(context, request):
    users = models.User.query.all()
    user_grid = h.PyramidGrid(users, ["title", "email"])

    groups = models.Group.query.all()
    group_grid = h.PyramidGrid(groups, models.Group.exposed_attrs())

    user_addform = h.mk_form(UserAddForm, context, request)
    if request.is_response(user_addform):
        return user_addform

    group_addform = h.mk_form(GroupAddForm, context, request)
    if request.is_response(group_addform):
        return group_addform

    return {
        "user_grid": user_grid,
        "user_addform": user_addform,
        "group_grid": group_grid,
        "group_addform": group_addform}


@view_config(route_name="principal_manage", permission="admin",
        renderer="edit.mako")
def principal_manage(context, request):
    if "user" in request.params:
        obj = models.User.get_by(id=request.params["user"])
        form = h.mk_form(UserEditForm, obj, request)
    elif "group" in request.params:
        obj = models.Group.get_by(id=request.params["group"])
        form = h.mk_form(GroupEditForm, obj, request)
    else:
        raise HTTPNotFound
    return form


@view_config(route_name="user_account", permission="view",
            renderer="user_account.mako")
def user_account(context, request):
    """
    Users preferences
    """
    user = request.user
    return h.mk_form(UserForm, user, request,
        extra={"sidebar_data": prefs_menu()})


@view_config(route_name="user_tenant_set", permission="view")
def user_tenant_set(context, request):
    """
    Method to help change tenants / groups.

    It sets the tenant if a "name" is in the params list and forwards the user
    to that tenants dashboard
    """
    id_ = group_from_request(request)

    def redirect(group):
        location = request.route_url("retailer_home", group=group)
        return HTTPFound(location=location)

    # NOTE: Check for tenant
    # * Check > update db with new tenant > forward
    # * No tenant > forward to current tenant or default
    if id_:
        # NOTE: Ok, so if there's a group and it's valid let's update in redis
        # and forward
        if request.user.has_group(id_):
            request.user.current_group_id = id_
            request.user.save()
            return redirect(id_)
        else:
            raise HTTPForbidden
    else:
        id_ = request.group or request.user.current_group
        if tenant:
            return redirect(id_)
        else:
            return HTTPFound(location=request.route_url("user_tenants"))


@view_config(route_name="user_tenants", permission="view",
        renderer="user_tenants_overview.mako")
def user_tenants(context, request):
    grid = h.PyramidGrid(request.user.retailers,
        ["group_name", "group_type"])
    return {"grid": grid}


def includeme(config):
    # NOTE: User links
    config.add_route("principal_manage", "/admin/principal")
    config.add_route("principals_manage", "/admin/principals")

    #config.add_route("group_manage", "/g/{group}")
    #config.add_route("user_delete", "@@admin/user/{id}/delete")

    # User specific
    config.add_route("user_account", "/settings/account")
    config.add_route("user_tenant_set", "/tenant/set")
    config.add_route("user_tenants", "/tenant")
