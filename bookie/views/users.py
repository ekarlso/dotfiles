from pprint import pformat
import logging
import pdb
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
from webhelpers.html.grid import Grid

from .. import models
from ..utils import _
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import get_url


LOG = logging.getLogger(__name__)


def roleset_validator(node, value):
    oneof = colander.OneOf(models.permission_names())
    [oneof(node, item) for item in value]


def group_validator(node, value):
    group = models.Group.by_group_name(value)
    if not group:
        raise colander.Invalid(node, _(u"No such group: ${group}",
                                mapping=dict(group=value)))

def _type(keys):
    return "group" if "group_name" in keys else "user"


def _add_from_db(schema):
    if "groups" in schema:
        schema["groups"]["group"].widget.values = \
            [dict(label=g.group_name, value=g.group_name) \
                for g in models.Group.query.all()]
    schema["permissions"].widget.values = models.permission_pairs()
    return schema


def _in(appstruct):
    """
    Helper to convert data from dict data to SA data
    """
    d = appstruct
    if "groups" in d:
        # NOTE: Convert groups for users
        d["groups"] = [models.Group.by_group_name(i) \
            for i in d["groups"]]

    pt = _type(d.keys())
    given_perms = d.pop("permissions")
    new_perms = [models.permission_create(pt, pn, d[pt + "_name"]) \
                        for pn in given_perms]
    if pt == "user":
        d["user_permissions"] = new_perms
    else:
        d["permissions"] = new_perms
    return d


class Groups(colander.SequenceSchema):
    group = colander.SchemaNode(
        colander.String(),
        title=_(u'Group'),
        validator=group_validator,
        missing=None,
        widget=AutocompleteInputWidget())


class UserPreferenceSchema(colander.Schema):
    user_name = colander.SchemaNode(colander.String())
    first_name = colander.SchemaNode(colander.String())
    middle_name = colander.SchemaNode(colander.String(), missing='')
    last_name = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=CheckedPasswordWidget(length="20"),
        description="Enter password...")
    email = colander.SchemaNode(colander.String())
    status = colander.SchemaNode(
        colander.Boolean(),
        title=_(u'Active'),
        description=_(u"Untick this to deactivate the account."))


class UserSchema(UserPreferenceSchema):
    groups = Groups(
        title=_(u'Groups'),
        missing=[],
        widget=SequenceWidget(min_len=1))
    permissions = colander.SchemaNode(
        deform.Set(allow_empty=True),
        validator=roleset_validator,
        missing=[],
        title=_(u"Permissions"),
        widget=CheckboxChoiceWidget())


class GroupSchema(colander.Schema):
    group_name = colander.SchemaNode(colander.String())
    permissions = colander.SchemaNode(
        deform.Set(allow_empty=True),
        validator=roleset_validator,
        missing=[],
        title=_(u"Global roles"),
        widget=CheckboxChoiceWidget())


class UserAddForm(AddFormView):
    item_type = _(u'User')
    buttons = (Button('add_user', _(u'Add User')),
               Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = UserSchema()
        _add_from_db(schema)
        schema.add(colander.SchemaNode(
            colander.Boolean(),
            name=u'send_email',
            title=_(u'Send password registration link'),
            default=True,
            ))
        return schema

    def add_user_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        _in(appstruct)
        appstruct['email'] = appstruct['email'] and appstruct['email'].lower()
        send_email = appstruct.pop('send_email', False)
        #get_principals()[name] = appstruct
        if send_email:
            email_set_password(get_principals()[name], self.request)
        #location = self.request.url.split('?')[0] + '?' + urlencode(
        #    {'extra': name})
        user = models.User().update(appstruct).save()
        self.request.session.flash(_(u'${title} added.',
                                     mapping=dict(title=user.title)),
                                     'success')
        return HTTPFound(location=get_url("auth_manage"))


class GroupAddForm(AddFormView):
    item_type = _(u'Group')
    buttons = (Button('add_group', _(u'Add Group')),
               Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = GroupSchema()
        _add_from_db(schema)
        return schema

    def add_group_success(self, appstruct):
        _in(appstruct)
        models.Group().update(appstruct).save()
        return HTTPFound(location=get_url("auth_manage"))


@view_config(route_name="auth_manage", permission="system.admin",
            renderer="bookie:templates/admin/auth_manage.pt")
def auth_manage(context, request):
    users = models.User.query.all()
    user_grid = PyramidGrid(users, ["user_name", "name", "email"])

    groups = models.Group.query.all()
    group_grid = PyramidGrid(groups, ["group_name", "member_count", "users"])

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


class UserForm(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return UserSchema()


class UserEditForm(UserForm):
    def schema_factory(self):
        schema = UserSchema()
        del schema["password"]
        _add_from_db(schema)
        return schema

    def save_success(self, appstruct):
        _in(appstruct)
        return super(UserForm, self).save_success(appstruct)

    def cancel_success(self, appstruct):
        self.request.session.flash(_(u'No changes made.'), 'info')
        return HTTPFound(location=get_url("auth_manage"))
    cancel_failure = cancel_success


class GroupEditForm(UserEditForm):
    def schema_factory(self):
        s = GroupSchema()
        _add_from_db(s)
        return GroupSchema()

    def save_success(self, appstruct):
        _in(appstruct)
        return super(UserForm, self).save_success(appstruct)



@view_config(route_name="user_manage", permission="system.admin",
            renderer="bookie:templates/admin/user_manage.pt")
def user_edit(request):
    user = models.User.query.filter_by(id=request.matchdict["id"]).one()
    return mk_form(UserEditForm, user, request)


@view_config(route_name="group_manage", permission="system.admin",
            renderer="bookie:templates/admin/group_manage.pt")
def group_edit(request):
    group = models.Group.query.filter_by(id=request.matchdict["id"]).one()
    return mk_form(GroupEditForm, group, request)


@view_config(route_name="user_prefs", permission="view",
            renderer="bookie:templates/admin/user_prefs.pt")
def user_preferences(request):
    user = request.user
    form = UserForm(user, request)()
    if request.is_response(form):
        return form
    return {"form": form["form"]}


def includeme(config):
    config.add_route("auth_manage", "@@admin/auth")
    config.add_route("user_manage", "@@admin/users/{id}")
    config.add_route("group_manage", "@@admin/groups/{id}")
    config.add_route("user_prefs", "@@prefs")
