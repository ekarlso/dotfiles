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
from webhelpers_extra import TemplateAPI as BaseTemplateAPI, template_api, add_renderer_globals

from bookie import get_settings
from bookie.utils import _, name_to_camel, camel_to_name

from . import importutils, navigation, utils


def is_root(context, request):
    return context is TemplateAPI(context, request).root


class TemplateAPI(BaseTemplateAPI):
    utils = utils

    @reify
    def site_title(self):
        value = get_settings().get('bookie.site_title')
        if not value:
            value = self.root.title
        return value

    @reify
    def page_title(self):
        view_title = self.name_to_camel(self.request.view) \
            if hasattr(self.request, "view") else ''
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


__all__ = ["template_api", "add_renderer_globals", "is_root",
           "TemplateAPI"]
