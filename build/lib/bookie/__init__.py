from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.mako_templating import renderer_factory as mako_factory
from sqlalchemy import engine_from_config

from . import models, security


ROOT_FACTORY = "bookie.security.RootFactory"
RESOURCE_FACTORY = "bookie.security.ResourceFactory"


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    models.configure_db(settings)

    authn_policy = AuthTktAuthenticationPolicy(
        "secret", callback=security.get_group)
    authz_policy = ACLAuthorizationPolicy()

    config = Configurator(settings=settings, root_factory=ROOT_FACTORY)

    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.set_request_property(security.add_user_to_request, 'user',
                                reify=True)

    config.add_static_view('static', 'static', cache_max_age=3600)

    config.add_route('index', '/')

    config.scan()
    return config.make_wsgi_app()

