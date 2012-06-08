from collections import defaultdict
from datetime import datetime
import hashlib
import re
import time
import urllib


from babel.dates import format_date, format_datetime, format_time

import colander
import deform
from deform import Button
from deform.widget import TextAreaWidget
from deform.widget import Widget
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid.i18n import get_localizer, get_locale_name, make_localizer
from pyramid.interfaces import ITranslationDirectories
from pyramid.location import inside, lineage
from pyramid.renderers import get_renderer, render
from pyramid.threadlocal import get_current_registry, get_current_request
from pyramid.view import render_view_to_response
from pyramid_deform import CSRFSchema, FormView
from webhelpers.html import grid, tags
from webhelpers import date

from bookie import get_settings
from bookie.utils import _


class PyramidGrid(grid.Grid):
    """
    Subclass of Grid that can handle header link generation for quick building
    of tables that support ordering of their contents, paginated results etc.
    """
    def generate_header_link(self, column_number, column, label_text):
        """
        This handles generation of link and then decides to call
        self.default_header_ordered_column_format or
        self.default_header_column_format based on if current column is the one
        that is used for sorting or not
        """

        # this will handle possible URL generation
        GET = dict(self.request.copy().GET) # needs dict() for py2.5 compat
        self.order_column = GET.pop("order_col", None)
        self.order_dir = GET.pop("order_dir", None)
        # determine new order
        if column == self.order_column and self.order_dir == "asc":
            new_order_dir = "dsc"
        else:
            new_order_dir = "asc"
        self.additional_kw['order_col'] = column
        self.additional_kw['order_dir'] = new_order_dir
        # generate new url
        new_url = self.url_generator(**self.additional_kw)
        # set label for header with link
        label_text = HTML.tag("a", href=new_url, c=label_text)
        # Is the current column the one we're ordering on?
        if column == self.order_column:
            return self.default_header_ordered_column_format(column_number,
                                                             column,
                                                             label_text)
        else:
            return self.default_header_column_format(column_number, column,
                                                     label_text)

class PyramidObjectGrid(PyramidGrid):
    """
    This grid will work well with sqlalchemy row instances
    """
    def default_column_format(self, column_number, i, record, column_name):
        class_name = "c%s" % (column_number)
        return tags.HTML.tag("td", getattr(record, column_name), class_=class_name)


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


# NOTE: Forms stuff underneath here
def get_appstruct(context, schema):
    appstruct = {}
    for field in schema.children:
        if hasattr(context, field.name):
            appstruct[field.name] = getattr(context, field.name)
    return appstruct


class Form(deform.Form):
    """A deform Form that allows 'appstruct' to be set on the instance.
    """
    def render(self, appstruct=None, readonly=False):
        if appstruct is None:
            appstruct = getattr(self, 'appstruct', colander.null)
        return super(Form, self).render(appstruct, readonly)


class BaseFormView(FormView):
    form_class = Form
    buttons = (Button('save', _(u'Save')), Button('cancel', _(u'Cancel')))
    success_message = _(u"Your changes have been saved.")
    success_url = None
    schema_factory = None
    use_csrf_token = True
    add_template_vars = ()

    def __init__(self, context, request, **kwargs):
        self.context = context
        self.request = request
        self.__dict__.update(kwargs)

    def __call__(self):
        if self.schema_factory is not None:
            self.schema = self.schema_factory()
        if self.use_csrf_token and 'csrf_token' not in self.schema:
            self.schema.children.append(CSRFSchema()['csrf_token'])
        result = super(BaseFormView, self).__call__()
        if isinstance(result, dict):
            result.update(self.more_template_vars())
        return result

    def cancel_success(self, appstruct):
        location = self.request.resource_url(self.context)
        return HTTPFound(location=location)
    cancel_failure = cancel_success

    def more_template_vars(self):
        result = {}
        for name in self.add_template_vars:
            result[name] = getattr(self, name)
        return result


class EditFormView(BaseFormView):
    add_template_vars = ('first_heading',)

    def before(self, form):
        form.appstruct = get_appstruct(self.context, self.schema)

    def save_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        self.edit(**appstruct)
        self.request.session.flash(self.success_message, 'success')
        location = self.success_url or self.request.resource_url(self.context)
        return HTTPFound(location=location)

    def edit(self, **appstruct):
        for key, value in appstruct.items():
            setattr(self.context, key, value)

    @reify
    def first_heading(self):
        return _(u'Edit <em>${title}</em>')


class AddFormView(BaseFormView):
    success_message = _(u"Successfully added item.")
    item_type = None
    add_template_vars = ('first_heading',)

    def save_success(self, appstruct):
        appstruct.pop('csrf_token', None)
        name = self.find_name(appstruct)
        new_item = self.context[name] = self.add(**appstruct)
        self.request.session.flash(self.success_message, 'success')
        location = self.success_url or self.request.resource_url(new_item)
        return HTTPFound(location=location)

    def find_name(self, appstruct):
        name = appstruct.get('name')
        if name is None:
            name = title_to_name(
                appstruct['title'], blacklist=self.context.keys())
        return name

    @reify
    def first_heading(self):
        context_title = getattr(self.request.context, 'title', None)
        type_title = self.item_type or self.add.type_info.title
        if context_title:
            return _(u'Add ${type} to <em>${title}</em>',)
        else:
            return _(u'Add ${type}',)


class CommaSeparatedListWidget(Widget):
    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (colander.null, None):
            cstruct = []
        return field.renderer(self.template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        return [item.strip() for item in pstruct.split(',') if item]


# NOTE: Util alike stuff underneath here
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
        if not "page_title" in event:
            event["page_title"] = get_settings()["bookie.site_title"]


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

