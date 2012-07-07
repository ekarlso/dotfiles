from os.path import dirname, join


from pyramid.events import subscriber
from pyramid.events import BeforeRender
from pyramid_webassets import IWebAssetsEnvironment
from webassets.loaders import YAMLLoader


def add_webassets(config):
    loader = YAMLLoader(join(dirname(__file__), 'resources.yaml'))
    bundles = loader.load_bundles()
    for name in bundles:
        print "LOADING", name
        config.add_webasset(name, bundles[name])


@subscriber(BeforeRender)
def add_global(event):
    environment = event['request'].registry.queryUtility(IWebAssetsEnvironment)
    event['environment'] = environment


def includeme(config):
    config.scan(__name__)
    config.include('pyramid_webassets')
    add_webassets(config)
