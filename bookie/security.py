import logging
import re

from pyramid import httpexceptions as exception
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import unauthenticated_userid, Authenticated, Allow
from sqlalchemy import orm

from . import message, models

LOG = logging.getLogger(__name__)


def get_groups(user_id, request):
    """Adds a group attribute to the request"""
    if user_id and hasattr(request, 'user'):
        db_groups = ['group:%s' % g.group_name for g in request.user.groups]
    groups = db_groups if len(db_groups) > 0 else []
    LOG.info("Groups for %s set to %s" % (user_id, ", ".join(groups)))
    return groups


def authtkt_factory(**settings):
    """Auth factory"""
    return AuthTktAuthenticationPolicy(
        secret=settings['bookie.secret2'], callback=get_groups)


def acl_factory(**settings):
    """A ACL Factory"""
    return ACLAuthorizationPolicy()


def get_user(request):
    """
    Method that looks up a user in the database and adds a attribute
    to the request
    """
    user = unauthenticated_userid(request)
    if user:
        return models.User.query.options(
                orm.joinedload("current_account"),
                orm.joinedload("groups")).\
            filter_by(user_name=user).one()


def get_account(request):
    """
    Return the current account from the url or current_account or accounts[0]
    if only 1 account
    """
    id_ = request.matchdict.get("account", None) if request.params else None

    user = request.user
    if user:
        if id_:
            return user.get_group(id_)
        else:
            if request.user.current_account:
                return request.user.current_account
            elif len(request.user.accounts) == 1:
                return request.user.accounts[0]


def reset():
    """
    Resetting methods for testing should be put here?
    """
    pass


class ResourceFactory(object):
    """
    A Resource ACL Factory
    """
    def __init__(self, request):
        self.__acl__ = []
        application_id = request.matchdict.get("resource_id") \
                         or request.params.get("resource_id")

        #if not application_id:
        #    raise exception.HTTPNotFound
        resource = models.Resource.by_resource_id(application_id)
        if not resource:
            raise exception.HTTPNotFound
        if resource and request.user:
            self.__acl__ = resource.__acl__
            for principal, perm_name in resource.perms_for_user(request.user):
                self.__acl__.append((Allow, principal, perm_name,))


class RootFactory(object):
    """
    Standard ACL factory
    """
    def __init__(self, request):
        self.__acl__ = [(Allow, Authenticated, u'view'), ]
        #general page factory - append custom non resource permissions
        if request.user:
            for principal, perm_name in request.user.permissions:
                self.__acl__.append((Allow, principal, perm_name,))


def includeme(config):
    settings = config.get_settings()
    # NOTE: Auth settings here
    authentication_policy = settings[
        'bookie.authn_policy_factory'][0](**settings)
    authorization_policy = settings[
        'bookie.authz_policy_factory'][0](**settings)
    session_factory = settings['bookie.session_factory'][0](**settings)
    if authentication_policy:
        config.set_authentication_policy(authentication_policy)
    if authorization_policy:
        config.set_authorization_policy(authorization_policy)
    config.set_session_factory(session_factory)

    config.set_request_property(get_account, 'account', reify=True)
    config.set_request_property(get_user, 'user', reify=True)


def email(user, request, route="reset_password", template="reset-password.mako",
        add_query={}):
    user.regenerate_security_code()
    sc = user.security_code
    user.save()

    query = dict(security_code=sc, user_name=user.user_name)
    query.update(add_query)
    url = request.route_url(route, _query=query)

    template_variables = dict(user=user, request=request, url=url)

    recipients = ['"%s" <%s>' % (user.display_name, user.email)]
    message.send(recipients=recipients, template=template, request=request,
            template_variables=template_variables)
