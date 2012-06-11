from deform import Form
from mako.template import Template
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.view import view_config
from pkg_resources import resource_filename


mako_template_dir = resource_filename('bookie', 'templates/deform/')

def mako_renderer(tname, **kw):
    from mako.template import Template
    def tra(term):
       return translator(_(term))
    template = Template(filename='%s%s.mako' %
                        (mako_template_dir, tname))
    return template.render(_=tra, **kw)


@view_config(route_name="index", renderer="bookie:templates/index.pt")
def index(request):
    return {"page_title": "Welcome to Bookie!"}


def includeme(config):
    config.add_static_view('static', 'bookie:static')
    config.include('pyramid_deform')
    config.include('deform_bootstrap')

    #Form.set_default_renderer(mako_renderer)

    config.add_route("index", "/")
