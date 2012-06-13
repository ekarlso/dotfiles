import colander
import deform
import logging
import pdb

import colander
import deform
from deform import Button
from deform.widget import TextAreaWidget
from deform.widget import Widget
from pyramid.decorator import reify
from pyramid.httpexceptions import HTTPFound
from pyramid_deform import CSRFSchema, FormView

from bookie.utils import _, title_to_name
from .utils import get_url


LOG = logging.getLogger(__name__)


def get_appstruct(context, schema):
    appstruct = {}
    for field in schema.children:
        if hasattr(context, field.name):
            appstruct[field.name] = getattr(context, field.name)
    return appstruct


def mk_form(form_cls, ctx, request):
    form = form_cls(ctx, request)()
    if request.is_response(form):
        return form
    return form



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
    cancel_url = None
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
        location = self.cancel_url or get_url(self.request.matched_route)
        self.request.session.flash(_(u'No changes made.'), 'info')
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
        self.context.update(appstruct)

    @reify
    def first_heading(self):
        return _(u'Edit <em>${title}</em>',
                mapping=dict(title=self.context.title))


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
        from bookie.views.helpers.utils import translate
        context_title = getattr(self.request.context, 'title', None)
        type_title = self.item_type or self.add.type_info.title
        if context_title:
            return _(
                    u'Add ${type} to <em>${title}</em>',
                    mapping=dict(type=translate(type_title),
                    title=context_title))
        else:
            return _(u'Add ${type}', mapping=dict(type=translate(type_title)))


class CommaSeparatedListWidget(Widget):
    def serialize(self, field, cstruct, readonly=False):
        if cstruct in (colander.null, None):
            cstruct = []
        return field.renderer(self.template, field=field, cstruct=cstruct)

    def deserialize(self, field, pstruct):
        if pstruct is colander.null:
            return colander.null
        return [item.strip() for item in pstruct.split(',') if item]


__all__ = ["get_appstruct", "mk_form", "EditFormView", "AddFormView"]
