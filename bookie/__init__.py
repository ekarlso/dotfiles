import pkg_resources
from pyramid.config import Configurator
from pyramid.events import BeforeRender
from pyramid.threadlocal import get_current_registry
from pyramid.util import DottedNameResolver
from pyramid_beaker import session_factory_from_settings

from . import models


CONF_DEFAULTS = {
    'bookie.templates.api': 'bookie.views.helpers.TemplateAPI',
    'bookie.configurators': '',
    "bookie.base_includes": " ".join([
        "bookie",
        "bookie.message",
        "bookie.resources",
        "bookie.security",
        "bookie.views",
        "bookie.views.bookings",
        "bookie.views.cache",
        "bookie.views.category",
        "bookie.views.customer",
        "bookie.views.entity",
        "bookie.views.misc",
        "bookie.views.login",
        "bookie.views.retailer",
        "bookie.views.users"]),
    'bookie.use_tables': '',
    'bookie.root_factory': 'bookie.security.RootFactory',
    'bookie.populators': 'bookie.populate.populate',
    'bookie.authn_policy_factory': 'bookie.security.authtkt_factory',
    'bookie.authz_policy_factory': 'bookie.security.acl_factory',
    'bookie.session_factory': 'bookie.beaker_session_factory',
    'bookie.caching_policy_chooser': (
        'bookie.views.cache.default_caching_policy_chooser')}


CONF_DOTTED = set([
    'bookie.configurators',
    'bookie.base_includes',
    'bookie.root_factory',
    'bookie.populators',
    'bookie.authn_policy_factory',
    'bookie.authz_policy_factory',
    'bookie.session_factory',
    'bookie.caching_policy_chooser'
    ])


def get_settings():
    """
    Allow to get settings but override with database ones
    """
    return get_current_registry().settings


def get_version():
    return pkg_resources.require("bookie")[0].version


def beaker_session_factory(**settings):
    return session_factory_from_settings(settings)


# TODO: Fix me!
def _resolve_dotted(d, keys=CONF_DOTTED):
    for key in keys:
        value = d[key]
        if not isinstance(value, basestring):
            continue
        new_value = []
        for dottedname in value.split():
            new_value.append(DottedNameResolver(None).resolve(dottedname))
        d[key] = new_value


def load_settings(global_config, **settings):
    for key, value in CONF_DEFAULTS.items():
        settings.setdefault(key, value)

    for key, value in settings.items():
        if isinstance(settings[key], basestring):
            settings[key] = unicode(value, 'utf8')

    _resolve_dotted(settings, keys=settings['bookie.configurators'])
    for func in settings['bookie.configurators']:
        func(settings)

    _resolve_dotted(settings)
    secret1 = settings['bookie.secret']
    settings.setdefault('bookie.secret2', secret1)
    return settings


def configure(global_config, **settings):
    settings = load_settings(global_config, **settings)
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

    models.configure_db()
    return config


def includeme(config):
    config.add_translation_dirs('bookie:locale')
    # NOTE: Should be reified
    from .views.helpers import add_renderer_globals
    config.add_subscriber(add_renderer_globals, BeforeRender)

    config.add_subscriber("bookie.utils.add_renderer_globals",
                        "pyramid.events.BeforeRender")
    config.add_subscriber("bookie.utils.add_localizer",
                        "pyramid.events.NewRequest")
    return config


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = configure(global_config, **settings)
    config.scan()
    return config.make_wsgi_app()
