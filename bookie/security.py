import logging
from pyramid import httpexceptions as exception
from pyramid.security import unauthenticated_userid, Authenticated, Allow, \
    Everyone

from .db import models

LOG = logging.getLogger(__name__)


def get_group(user_id, request):
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


def add_user_to_request(request):
    user = unauthenticated_userid(request)
    if user:
        return models.User.by_user_name(user)


def reset():
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
