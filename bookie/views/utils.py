from collections import defaultdict
from datetime import datetime
import hashlib
import urllib

from babel.dates import format_date, format_datetime, format_time
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer, get_locale_name, make_localizer
from pyramid.interfaces import ITranslationDirectories
from pyramid.location import inside, lineage
from pyramid.renderers import get_renderer, render
from pyramid.threadlocal import get_current_registry, get_current_request
from pyramid.view import render_view_to_response


def template_api(context, request, **kwargs):
    return get_settings()['bookie.templates.api'][0](
        context, request, **kwargs)


def render_view(context, request, name='', secure=True):
    response = render_view_to_response(context, request, name, secure)
    if response is not None:
        return response.ubody


def add_renderer_globals(event):
    if event['renderer_name'] != 'json':
        request = event['request']
        api = getattr(request, 'template_api', None)
        if api is None and request is not None:
            api = template_api(event['context'], event['request'])
        event['api'] = api


def is_root(context, request):
    return context is TemplateAPI(context, request).root


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
    # Instead of overriding these, consider using the
    # 'bookie.overrides' variable.
    BARE_MASTER = 'bookie:templates/master-bare.pt'
    VIEW_MASTER = 'bookie:templates/view/master.pt'
    EDIT_MASTER = 'bookie:templates/edit/master.pt'
    SITE_SETUP_MASTER = 'bookie:templates/site-setup/master.pt'

    body_css_class = ''

    def __init__(self, context, request, bare=None, **kwargs):
        self.context, self.request = context, request

        if getattr(request, 'template_api', None) is None:
            request.template_api = self

        self.S = get_settings()
        if request.is_xhr and bare is None:
            bare = True  # use bare template that renders just the content area
        self.bare = bare
        self.__dict__.update(kwargs)

    def macro(self, asset_spec, macro_name='main'):
        if self.bare and asset_spec in (
            self.VIEW_MASTER, self.EDIT_MASTER, self.SITE_SETUP_MASTER):
            asset_spec = self.BARE_MASTER
        return get_renderer(asset_spec).implementation().macros[macro_name]

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
            format = self.S['bookie.date_format']
        return format_date(d, format=format, locale=self.locale_name)

    def format_datetime(self, dt, format=None):
        if format is None:
            format = self.S['bookie.datetime_format']
        if not isinstance(dt, datetime):
            dt = datetime.fromtimestamp(dt)
        return format_datetime(dt, format=format, locale=self.locale_name)

    def format_time(self, t, format=None):
        if format is None:
            format = self.S['bookie.time_format']
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
