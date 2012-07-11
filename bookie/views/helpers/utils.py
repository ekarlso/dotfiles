from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.interfaces import ITranslationDirectories
from pyramid.view import render_view_to_response
from webhelpers.html import grid, HTML, literal, tags
from webhelpers import date

from bookie import get_settings
from bookie.utils import _


"""
What goes here?

Utlities that help for HTML / View things.
Other things go into <pkg.utils>
"""


def render_view(context, request, name='', secure=True):
    response = render_view_to_response(context, request, name, secure)
    if response is not None:
        return response.ubody
