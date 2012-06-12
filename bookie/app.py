from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.config import Configurator
from pyramid.events import BeforeRender
from pyramid.threadlocal import get_current_registry
from pyramid.util import DottedNameResolver
from pyramid_beaker import session_factory_from_settings

from . import db, security, utils


def authtkt_factory(**settings):
    return AuthTktAuthenticationPolicy(
        secret=settings['bookie.secret2'], callback=security.get_group)


def acl_factory(**settings):
    return ACLAuthorizationPolicy()


def beaker_session_factory(**settings):
    return session_factory_from_settings(settings)


conf_defaults = {
    'bookie.templates.api': 'bookie.views.helpers.TemplateAPI',
    "bookie.base_includes": " ".join([
        "bookie.app",
        "bookie.views",
        "bookie.views.entities",
        "bookie.views.login",
        "bookie.views.users"]),
    'bookie.use_tables': '',
    'bookie.root_factory': 'bookie.security.RootFactory',
    'bookie.authn_policy_factory': 'bookie.authtkt_factory',
    'bookie.authz_policy_factory': 'bookie.acl_factory',
    'bookie.session_factory': 'bookie.beaker_session_factory',
    'bookie.caching_policy_chooser': (
        'bookie.views.cache.default_caching_policy_chooser')}


conf_dotted = set([
    'bookie.templates.api',
    'bookie.base_includes',
    'bookie.root_factory',
    'bookie.authn_policy_factory',
    'bookie.authz_policy_factory',
    'bookie.session_factory',
    ])


# TODO: Fix me!
@utils.request_cache(lambda: None)
def get_settings():
    #session = DBSession()
    #db_settings = session.query(Settings).order_by(desc(Settings.id)).first()
    #if db_settings is not None:
        #reg_settings = dict(get_current_registry().settings)
        #reg_settings.update(db_settings.data)
        #return reg_settings
    #else:
    return get_current_registry().settings


def _resolve_dotted(d, keys=conf_dotted):
    for key in keys:
        value = d[key]
        if not isinstance(value, basestring):
            continue
        new_value = []
        for dottedname in value.split():
            new_value.append(DottedNameResolver(None).resolve(dottedname))
        d[key] = new_value


def base_configure(global_config, **settings):
    for key, value in conf_defaults.items():
        settings.setdefault(key, value)

    for key, value in settings.items():
        if isinstance(settings[key], basestring):
            settings[key] = unicode(value, 'utf8')

    _resolve_dotted(settings)

    secret1 = settings['bookie.secret']
    settings.setdefault('bookie.secret2', secret1)

    # We'll process ``pyramid_includes`` later by hand, to allow
    # overrides of configuration from ``bookie.base_includes``:
    pyramid_includes = settings.pop('pyramid.includes', '')

    config = Configurator(settings=settings,
                        root_factory=settings['bookie.root_factory'][0])
    config.begin()
    config.registry.settings['pyramid.includes'] = pyramid_includes

    # Include modules listed in 'bookie.base_includes':
    for module in settings['bookie.base_includes']:
        config.include(module)
    config.commit()

    # Modules in 'pyramid.includes' may override 'bookie.base_includes':
    if pyramid_includes:
        for module in pyramid_includes.split():
            config.include(module)
        config.commit()

    db.configure_db(settings)
    return config


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

    # NOTE: Anything else that's not in base here..
    config.add_translation_dirs('bookie:locale')
    config.set_request_property(security.get_user, 'user', reify=True)
    from .views.helpers import add_renderer_globals
    config.add_subscriber(add_renderer_globals, BeforeRender)
    return config


__all__ = ["authtkt_factory", "acl_factory", "beaker_session_factory", "get_settings",
          "_resolve_dotted", "base_configure"]
