import logging
from pyramid import httpexceptions as exception
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import unauthenticated_userid, Authenticated, Allow
from sqlalchemy.orm import exc

from . import models

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
        return models.User.by_user_name(user)


def get_group(request):
    """
    Return the current working group
    """
    g = request.matchdict.get("group", None) if request.matchdict else None
    if g:
        if type(g) == int:
            filter_by = {"group_id": g}
        else:
            filter_by = {"group_name": g}
        try:
            return models.Group.query.filter_by(**filter_by).one()
        except exc.NoResultFound:
            raise exception.HTTPNotFound


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
            if request.group and not request.user.has_group(request.group.id):
                raise exception.HTTPNotFound
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

    config.set_request_property(get_group, 'group', reify=True)
    config.set_request_property(get_user, 'user', reify=True)
