from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import ITranslationDirectories
from pyramid.threadlocal import get_current_registry, get_current_request
from pyramid.view import render_view_to_response
from pyramid.url import route_url as _url
from webhelpers.html import grid, HTML, literal, tags
from webhelpers import date

from bookie import get_settings
from bookie.utils import _


"""
What goes here?

Utlities that help for HTML / View things.
Other things go into <pkg.utils>
"""


def get_url(route, *args, **kw):
    """
    Get a URL
    """
    request = get_current_request()
    location = "%s" % _url(route, request, *args, **kw)
    return location


def create_anchor(string, view=None, *args, **kw):
    """
    Create a anchor towards a route

    :param view: The view_name to use
    """

    return literal('<a href="%s">%s</a>') % \
        (get_url(view, *args, **kw), string)


def render_view(context, request, name='', secure=True):
    response = render_view_to_response(context, request, name, secure)
    if response is not None:
        return response.ubody
