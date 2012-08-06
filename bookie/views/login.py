from datetime import datetime
import logging
import sys
import urllib

import colander
import deform
from deform.widget import CheckedPasswordWidget, HiddenWidget
from formencode.validators import Email
from pyramid.encode import urlencode
import pyramid.httpexceptions as exceptions
from pyramid.security import authenticated_userid, remember, forget
from pyramid.url import resource_url
from pyramid.view import view_config

from .. import models, security
from ..utils import _
from . import helpers as h, users

LOG = logging.getLogger(__name__)


@view_config(route_name='login', renderer='login.mako')
def login(context, request):
    login_url = urllib.unquote(request.route_url("login"))
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get("came_from", referrer)

    user_name, password = u'', u''
    if 'submit' in request.POST:
        user_name = request.params['user_name'].lower()
        password = request.params['password']
        user = models.User.by_user_name(user_name)

        if (user is not None and user.status == 1 and
                user.check_password(password)):
            headers = remember(request, user_name)
            request.session.flash(
                _(u"Welcome, ${user}!", mapping=dict(user=user.display_name)))
            user.last_login_date = datetime.now()
            return exceptions.HTTPFound(location=came_from, headers=headers)
        request.session.flash("error;" + _(u"Login failed."))

    if 'reset-password' in request.POST:
        user_name = request.params['user_name']
        user = models.User.by_user_name(user_name)
        if user is not None:
            security.email(user, request)
            request.session.flash(_(
                "info;"
                u"You should receive an email with a link to reset your "
                u"password momentarily."))
        else:
            request.session.flash("error;" + _(u"That username or email is not known to us."))

    return {
        'url': request.route_url("login"),
        'came_from': came_from,
        'user_name': user_name,
        'password': password,
        }


@view_config(route_name='logout')
def logout(context, request):
    """
    Logout
    """
    headers = forget(request)
    request.session.flash(_(u"You have been logged out."))
    location = request.params.get('came_from', request.application_url)
    return exceptions.HTTPFound(location=location, headers=headers)


class SetPasswordSchema(colander.MappingSchema):
    password = colander.SchemaNode(
        colander.String(),
        title=_(u'Password'),
        validator=colander.Length(min=5),
        widget=CheckedPasswordWidget(),
        )
    user_name = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        )
    security_code = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        missing=None,
        )
    continue_to = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        missing=colander.null,
        )


@view_config(route_name="reset_password", renderer="edit.mako")
def reset_password(context, request,
                 success_msg=_(u"You've reset your password successfully.")):
    form = deform.Form(SetPasswordSchema(), buttons=(deform.Button('submit', _(u'Submit')),))
    rendered_form = None

    if 'submit' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except deform.ValidationFailure, e:
            request.session.flash("error;" + _(u"There was an error."))
            rendered_form = e.render()
        else:
            security_code = appstruct['security_code']
            user_name = appstruct['user_name']

            user = models.User.by_user_name_and_security_code(user_name, security_code)

            if user:
                user.set_password(appstruct["password"])
                headers = remember(request, user.user_name)

                location = (appstruct['continue_to'] or request.route_url("user_account"))
                request.session.flash("success;" + success_msg)
                return exceptions.HTTPFound(location=location, headers=headers)
            else:
                request.session.flash(
                    _("error;" + u"Your password reset token may have expired."))

    if rendered_form is None:
        params = [("security_code", request.user.security_code),
                ("user_name", request.user.user_name)] if request.user \
                        else request.params.items()
        rendered_form = form.render(params)

    return {"page_title": _(u"Reset your password - ${title}"),
            "sidebar_data": users.prefs_menu(), "form": rendered_form}


class SignupSchema(colander.Schema):
    user_name = colander.SchemaNode(
            colander.String(),
            title=_(u"Username"))
    email = colander.SchemaNode(
            colander.String(),
            title=_(u"E-Mail"))
    password = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(min=5, max=100),
            widget=CheckedPasswordWidget(length="20"),
            title=_(u"Password"),
            description=_(u"Enter password..."))

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


class SignupForm(h.AddFormView):
    item_type = _("Signup")
    buttons = (deform.Button("signup", _("Signup")),
            deform.Button("cancel", _("Cancel")))

    def schema_factory(self):
        return SignupSchema()

    @property
    def cancel_url(self):
        return self.request.route_url("index")

    def signup_success(self, appstruct):
        appstruct.pop('csrf_token', None)

        appstruct["status"] = 0
        user = models.User().from_dict(appstruct)
        user.set_password(appstruct.pop("password"))
        user.save()

        security.email(user, self.request, route="account_activate",
                template="signup.mako")

        self.request.session.flash(_("Signup successful."
            "You will receive a e-mail for further steps!"))
        location = self.request.route_url("account_activate")
        return exceptions.HTTPFound(location=location)


@view_config(route_name="account_signup", renderer="account_signup.mako")
def signup(context, request):
    """
    Signup form and mail re-send
    """
    return h.mk_form(SignupForm, context, request)


@view_config(route_name="account_activate", renderer="account_activate.mako")
def activate(context, request):
    """
    Account activation
    """
    try:
        user_name = request.params["user_name"]
        security_code = request.params["security_code"]
    except KeyError:
        raise exceptions.HTTPForbidden("Invalid security code or username")

    user = models.User.by_user_name_and_security_code(user_name, security_code)

    if user:
        if user.status == 1:
            msg = "warning;Account already activated!"
        else:
            user.status = 1
            user.save()
            msg = "warning;Account activated!"

        request.session.flash(msg)
        headers = remember(request, user_name)
        return exceptions.HTTPFound(location=request.route_url("index"), headers=headers)
    else:
        raise exceptions.HTTPForbidden



@view_config(context=exceptions.HTTPForbidden, accept="text/html")
@view_config(context=exceptions.HTTPForbidden)
def forbidden_redirect(context, request):
    if authenticated_userid(request):
        location = request.application_url + '/@@forbidden'
    else:
        location = request.route_url("login", _query=dict(
            came_from=urlencode({'came_from': request.url})))
    return exceptions.HTTPFound(location=location)


def forbidden_view(request):
    return request.exception


def includeme(config):
    config.add_view(name='forbidden', renderer='forbidden.mako')
    config.add_route("login", "/user/login")
    config.add_route("logout", "/user/logout")
    config.add_route("reset_password", "/user/reset_password")
    config.add_route("account_signup", "/user/signup")
    config.add_route("account_activate", "/user/activate")
