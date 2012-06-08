from collections import defaultdict
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
from bookie.utils import _

from .utils import render_view


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
        if not "page_title" in event:
            event["page_title"] = get_settings()["bookie.site_title"]


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

    @classmethod
    def resource_url(cls, resource):
        get_

    def _resource(self, resource):
        has_package = re.search("^\w+:", resource)
        if not has_package:
            resource = "%s:%s" % (self.__module__.split(".")[0], resource)
        return self.request.static_url(resource)

    def _resource_html(self, format, resource):
        def _html(p):
            return format % self._resource(p)

        if type(resource) == list:
            string = "\n".join([_html(p) for p in resource])
        else:
            string = _html(string)
        return string

    def css_link(self, resource, format=CSS_LINK):
        return self._resource_html(format, resource)

    def script_link(self, resource, format=SCRIPT_LINK):
        return self._resource_html(format, resource)

    @reify
    def site_title(self):
        value = get_settings().get('bookie.site_title')
        if not value:
            value = self.root.title
        return value

    @reify
    def page_title(self):
        view_title = self.request.view_name.replace('_', ' ').title()
        if view_title:
            view_title += u' '
        view_title += self.context.title
        return u'%s - %s' % (view_title, self.site_title)

    def url(self, context=None, *elements, **kwargs):
        if context is None:
            context = self.context
        return self.request.resource_url(context, *elements, **kwargs)

    @reify
    def root(self):
        return self.lineage[-1]

    @reify
    def lineage(self):
        return list(lineage(self.context))

    @reify
    def breadcrumbs(self):
        return reversed(self.lineage)

    #def has_permission(self, permission, context=None):
    #    if context is None:
    #        context = self.context
    #    return has_permission(permission, context, self.request)

    def render_view(self, name='', context=None, request=None, secure=True,
                    bare=True):
        if context is None:
            context = self.context
        if request is None:
            request = self.request

        before = self.bare
        try:
            self.bare = bare
            html = render_view(context, request, name, secure)
        finally:
            self.bare = before
        return TemplateStructure(html)

    def render_template(self, renderer, **kwargs):
        return TemplateStructure(render(renderer, kwargs, self.request))

    #def list_children(self, context=None, permission='view'):
    #    if context is None:
    #        context = self.context
    #    children = []
    #    if hasattr(context, 'values'):
    #        for child in context.values():
    #            if (not permission or
    #                has_permission(permission, child, self.request)):
    #                children.append(child)
    #    return children

    inside = staticmethod(inside)

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

    def get_type(self, name):
        for class_ in get_settings()['bookie.available_types']:
            if class_.type_info.name == name:
                return class_

    #def find_edit_view(self, item):
    #    view_name = self.request.view_name
    #    if not view_permitted(item, self.request, view_name):
    #        view_name = u'edit'
    #    if not view_permitted(item, self.request, view_name):
    #        view_name = u''
    #    return view_name

    #@reify
    #def edit_links(self):
    #    if not hasattr(self.context, 'type_info'):
    #        return []
    #    return [l for l in self.context.type_info.edit_links
    #            if l.permitted(self.context, self.request)]

    #def more_links(self, name):
    #    return [l for l in getattr(self, name)
    #            if l.permitted(self.context, self.request)]


__all__ = ["template_api", "add_renderer_globals", "is_root", 
           "TemplateAPI", "CSS_LINK", "SCRIPT_LINK"]
