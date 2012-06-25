from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer, get_locale_name, make_localizer
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
    request = get_current_request()
    location = "%s" % _url(route, request, *args, **kw)
    return location


def menu_item(title, route, *args, **kw):
    return {"title": title, "url": get_url(route, *args, **kw)}


def menu_came_from(request, title="Go Back"):
    came_from = request.params.get("came_from", None)
    return dict(icon="arrow-left", title=title, url=came_from) \
        if came_from else {}


def create_anchor(string, route=None, *args, **kw):
    return literal('<a href="%s">%s</a>') % \
        (get_url(route, *args, **kw), string)


def wrap_td(string):
    return HTML.td(literal(string))


def when_normalize(col_num, i, item):
    time = item.timestamp
    label = date.distance_of_time_in_words(time,
        datetime.utcnow(),
        granularity='minute')
    if item.request_id:
        href = request.route_url('logs',
            _query=(('request_id', item.request_id,),), page=1)
        return h.HTML.td(h.link_to(label, href,
            title=time.strftime('%Y-%m-%d %H:%M:%S'),
            class_='c%s' % col_num))
    else:
       return HTML.td(label, title=time.strftime('%Y-%m-%d %H:%M:%S'),
            class_='c%s' % col_num)


def render_view(context, request, name='', secure=True):
    response = render_view_to_response(context, request, name, secure)
    if response is not None:
        return response.ubody
