from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer, get_locale_name, make_localizer
from pyramid.interfaces import ITranslationDirectories
from pyramid.threadlocal import get_current_registry, get_current_request
from pyramid.view import render_view_to_response
from pyramid.url import route_url as _url
from webhelpers.html import grid, tags
from webhelpers import date

from bookie import get_settings
from bookie.utils import _


def get_url(route, **kw):
    request = get_current_request()
    location = "%s" % _url(route, request, **kw)
    return location


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


def get_localizer_for_locale_name(locale_name):
    registry = get_current_registry()
    tdirs = registry.queryUtility(ITranslationDirectories, default=[])
    return make_localizer(locale_name, tdirs)


def translate(*args, **kwargs):
    request = get_current_request()
    if request is None:
        localizer = get_localizer_for_locale_name('en')
    else:
        localizer = get_localizer(request)
    return localizer.translate(*args, **kwargs)


__all__ = ["get_url", "when_normalize", "render_view",
            "get_localizer_for_locale_name", "translate"]
