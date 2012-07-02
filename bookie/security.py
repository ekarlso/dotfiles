import logging
from pyramid import httpexceptions as exception
from pyramid.security import unauthenticated_userid, Authenticated, Allow, \
    Everyone

from . import models

LOG = logging.getLogger(__name__)


def get_groups(user_id, request):
    if user_id and hasattr(request, 'user'):
        db_groups = ['group:%s' % g.group_name for g in request.user.groups]
    groups = db_groups if len(db_groups) > 0 else []
    LOG.info("Groups for %s set to %s" % (user_id, ", ".join(groups)))
    return groups


def authtkt_factory(**settings):
    return AuthTktAuthenticationPolicy(
        secret=settings['bookie.secret2'], callback=get_group)


def acl_factory(**settings):
    return ACLAuthorizationPolicy()


def get_user(request):
    user = unauthenticated_userid(request)
    if user:
        return models.User.by_user_name(user)


def get_group(request):
    """
    Return the current working group
    """
    if request.matchdict:
        return request.matchdict.get("group", None)


def reset():
    """
    Resetting methods for testing should be put here?
    """
    pass


class ResourceFactory(object):
    def __init__(self, request):
        self.__acl__ = []
        application_id = request.matchdict.get("resource_id") \
                         or request.params.get("resource_id")

        #if not application_id:
        #    raise exception.HTTPNotFound
        self.resource = models.Resource.by_resource_id(application_id)
        if not self.resource:
            raise exception.HTTPNotFound
        if self.resource and request.user:
            self.__acl__ = self.resource.__acl__
            for perm_user, perm_name in self.resource.perms_for_user(request.user):
                self.__acl__.append((Allow, perm_user, perm_name,))


class RootFactory(object):
    def __init__(self, request):
        self.__acl__ = [(Allow, Authenticated, u'view'), ]
        #general page factory - append custom non resource permissions
        if request.user:
            for perm_user, perm_name in request.user.permissions:
                self.__acl__.append((Allow, perm_user, perm_name,))


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
