from .app import *


def get_version():
    return pkg_resources.require("bookie")[0].version


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = base_configure(global_config, **settings)
    config.scan()
    return config.make_wsgi_app()
