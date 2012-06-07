from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.view import view_config


@view_config(route_name="index", renderer="index.html")
def index(request):
    #return HTTPFound()
    return {"page_title": "Welcome to Bookie!"}


def includeme(config):
    config.add_static_view('static', 'bookie:static')
    config.include('pyramid_deform')
    config.include('deform_bootstrap')

    config.add_route("index", "/")
