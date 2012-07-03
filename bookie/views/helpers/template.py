from collections import defaultdict
from functools import wraps
import hashlib
import re
import urllib

from babel.dates import format_date, format_datetime, format_time
from pyramid.decorator import reify
from pyramid.location import inside, lineage
from pyramid.renderers import get_renderer, render
from pyramid.threadlocal import get_current_registry, get_current_request
from pyramid.url import resource_url

from bookie import get_settings
from bookie.utils import _, name_to_camel, camel_to_name

from . import navigation, utils


def template_api(context, request, **kwargs):
    return get_settings()['bookie.templates.api'][0](
        context, request, **kwargs)


def is_root(context, request):
    return context is TemplateAPI(context, request).root


def add_renderer_globals(event):
    if event['renderer_name'] != 'json':
        request = event['request']
        api = getattr(request, 'template_api', None)
        if api is None and request is not None:
            api = template_api(event['context'], event['request'])
        event['api'] = api
        if not "sub_title" in event:
            event["sub_title"] = None


CSS_LINK = '<link rel="stylesheet" type="text/css" href="%s"/>'
SCRIPT_LINK = '<script src="%s"></script>'


class TemplateStructure(object):
    def __init__(self, html):
        self.html = html

    def __html__(self):
        return self.html
    __unicode__ = __html__

    def __getattr__(self, key):
        return getattr(self.html, key)


class TemplateAPI(object):
    """This implements the 'api' object that's passed to all
    templates.

    Use dict-access as a shortcut to retrieve template macros from
    templates.
    """
    def __init__(self, context, request, bare=None, **kwargs):
        self.context, self.request = context, request

        if getattr(request, 'template_api', None) is None:
            request.template_api = self

        self.settings = get_settings()
        if request.is_xhr and bare is None:
            bare = True  # use bare template that renders just the content area
        self.bare = bare
        self.__dict__.update(kwargs)

    utils = utils

    # NOTE: HTML / Link helpers
    def _resource_html(self, format, resource):
        def _link(p):
            has_package = re.search("^\w+:", p)
            if not has_package:
                p = "%s:%s" % (self.__module__.split(".")[0], p)
            return self.request.static_url(p)

        def _html(p):
            return format % _link(p)

        if type(resource) == list:
            string = "\n".join([_html(p) for p in resource])
        else:
            string = _html(string)
        return string

    def css_link(self, resource, format=CSS_LINK):
        return self._resource_html(format, resource)

    def script_link(self, resource, format=SCRIPT_LINK):
        return self._resource_html(format, resource)

    def resource_url(self, context=None, *elements, **kwargs):
        if context is None:
            context = self.context
        return self.request.resource_url(context, *elements, **kwargs)

    def avatar_url(self, user=None, size="14", default_image='identicon'):
        if user is None:
            user = self.request.user
        email = user.email
        if not email:
            email = user.name
        h = hashlib.md5(email).hexdigest()
        query = {'default': default_image, 'size': str(size)}
        url = 'https://secure.gravatar.com/avatar/%s?%s' % (
            h, urllib.urlencode(query))
        return url

    def dropdown(self, data):
        return menu.Dropdown(self.context, self.request, data)

    def nav(self, data):
        return menu.Navigation(self.context, self.request, data)

    def sidebar(self, data):
        return menu.Sidebar(self.context, self.request, data)

    @reify
    def site_title(self):
        value = get_settings().get('bookie.site_title')
        if not value:
            value = self.root.title
        return value

    @reify
    def page_title(self):
        view_title = self.name_to_camel(self.request.view_name) \
            if hasattr(self.request, "view_name") else ''
        if view_title:
            view_title += u' '
        view_title += getattr(self.context, "title", "")
        if view_title == '':
            view_title = self.site_title
        return u'%s' % (view_title)

    # NOTE: Render helpers
    def render_view(self, name='', context=None, request=None, secure=True,
                    bare=True):
        if context is None:
            context = self.context
        if request is None:
            request = self.request

        before = self.bare
        try:
            self.bare = bare
            html = self.utils.render_view(context, request, name, secure)
        finally:
            self.bare = before
        return TemplateStructure(html)

    def render_template(self, renderer, **kwargs):
        return TemplateStructure(render(renderer, kwargs, self.request))

    @reify
    def root(self):
        return self.lineage[-1]

    @reify
    def lineage(self):
        return list(lineage(self.context))

    @reify
    def breadcrumbs(self):
        return reversed(self.lineage)

    def list_children(self, context=None, permission='view'):
        if context is None:
            context = self.context
        children = []
        if hasattr(context, 'values'):
            for child in context.values():
                if (not permission or
                    has_permission(permission, child, self.request)):
                    children.append(child)
        return children

    inside = staticmethod(inside)

    # NOTE: Security stuff
    def has_permission(self, permission, context=None):
        if context is None:
            context = self.context
        return has_permission(permission, context, self.request)

    # NOTE: Formatting / Conversion
    @reify
    def locale_name(self):
        return get_locale_name(self.request)

    def format_date(self, d, format=None):
        if format is None:
            format = self.settings['bookie.date_format']
        return format_date(d, format=format, locale=self.locale_name)

    def format_datetime(self, dt, format=None):
        if format is None:
            format = self.settings['bookie.datetime_format']
        if not isinstance(dt, datetime):
            dt = datetime.fromtimestamp(dt)
        return format_datetime(dt, format=format, locale=self.locale_name)

    def format_time(self, t, format=None):
        if format is None:
            format = self.settings['bookie.time_format']
        return format_time(t, format=format, locale=self.locale_name)

    def name_to_camel(self, *args, **kw):
        return name_to_camel(*args, **kw)

    def camel_to_name(self, *args, **kw):
        return camel_to_name(*args, **kw)



__all__ = ["template_api", "add_renderer_globals", "is_root",
           "TemplateAPI", "CSS_LINK", "SCRIPT_LINK"]
