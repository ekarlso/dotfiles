from datetime import datetime
import logging
import sys
import urllib

import colander
from deform import Button, Form, ValidationFailure
from deform.widget import CheckedPasswordWidget, HiddenWidget
from formencode.validators import Email
from pyramid.encode import urlencode
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.security import authenticated_userid, remember, forget
from pyramid.url import resource_url
from pyramid.view import view_config

from ..db import models
from ..utils import _

LOG = logging.getLogger(__name__)


@view_config(route_name='login', renderer='bookie:templates/login.pt')
def login(context, request):
    login_url = urllib.unquote(request.route_url("login"))
    referrer = request.url
    if referrer == login_url:
        referrer = '/' # never use the login form itself as came_from
    came_from = request.params.get("came_from", referrer)

    login, password = u'', u''
    #LOG.debug("User %s" % request.user.user_name)

    if 'submit' in request.POST:
        login = request.params['login'].lower()
        password = request.params['password']
        user = models.User.by_user_name(login)

        if (user is not None and user.status == 1 and
            user.check_password(password)):
            headers = remember(request, login)
            request.session.flash(
                _(u"Welcome, ${user}!",
                  mapping=dict(user=unicode(user) or user.user_name)), 'success')
            user.last_login_date = datetime.now()
            return HTTPFound(location=came_from, headers=headers)
        LOG.debug("Failed login attempt %s" % user)
        request.session.flash(_(u"Login failed."), 'error')

    if 'reset-password' in request.POST:
        login = request.params['login']
        user = models.User.by_user_name(login)
        if user is not None:
            email_set_password(
                user, request,
                template_name='bookie:templates/email-reset-password.pt')
            request.session.flash(_(
                u"You should receive an email with a link to reset your "
                u"password momentarily."), 'success')
        else:
            request.session.flash(
                _(u"That username or email is not known to us."), 'error')

    return {
        'url': request.application_url + '/@@login',
        'came_from': came_from,
        'login': login,
        'password': password,
        }


@view_config(route_name='logout')
def logout(context, request):
    headers = forget(request)
    request.session.flash(_(u"You have been logged out."))
    location = request.params.get('came_from', request.application_url)
    return HTTPFound(location=location, headers=headers)


class SetPasswordSchema(colander.MappingSchema):
    password = colander.SchemaNode(
        colander.String(),
        title=_(u'Password'),
        validator=colander.Length(min=5),
        widget=CheckedPasswordWidget(),
        )
    token = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        )
    email = colander.SchemaNode(
        colander.String(),
        title=_(u'E-Mail'),
        widget=HiddenWidget(),
        )
    continue_to = colander.SchemaNode(
        colander.String(),
        widget=HiddenWidget(),
        missing=colander.null,
        )


@view_config(name="set-password", renderer="bookie:template/edit/simpleform.pt")
def set_password(context, request,
                 success_msg=_(u"You've reset your password successfully.")):
    form = Form(SetPasswordSchema(), buttons=(Button('submit', _(u'Submit')),))
    rendered_form = None

    if 'submit' in request.POST:
        try:
            appstruct = form.validate(request.POST.items())
        except ValidationFailure, e:
            request.session.flash(_(u"There was an error."), 'error')
            rendered_form = e.render()
        else:
            token = appstruct['token']
            email = appstruct['email']
            user = _find_user(email)
            if (user is not None and
                validate_token(user, token) and
                token == user.confirm_token):
                password = appstruct['password']
                user.password = get_principals().hash_password(password)
                user.confirm_token = None
                headers = remember(request, user.name)
                user.last_login_date = datetime.now()

                location = (appstruct['continue_to'] or
                            resource_url(context, request))
                request.session.flash(success_msg, 'success')
                return HTTPFound(location=location, headers=headers)
            else:
                request.session.flash(
                    _(u"Your password reset token may have expired."), 'error')

    if rendered_form is None:
        rendered_form = form.render(request.params.items())

    return {"page_title": _(u"Reset your password - ${title}"),
            "form": rendered_form}


@view_config(context=HTTPForbidden, accept="text/html")
@view_config(context=HTTPForbidden)
def forbidden_redirect(context, request):
    if authenticated_userid(request):
        location = request.application_url + '/@@forbidden'
    else:
        location = request.application_url + '/@@login?' + \
            urlencode({'came_from': request.url})
    return HTTPFound(location=location)


def forbidden_view(request):
    return request.exception


def includeme(config):
    config.add_view(name='forbidden', renderer='bookie:templates/forbidden.pt')
    config.add_route("login", "/@@login")
    config.add_route("logout", "/@@logout")
