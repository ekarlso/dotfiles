import logging
import re

import colander
import deform
import deform
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, CheckboxChoiceWidget, PasswordWidget, SequenceWidget

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from .. import models
from ..utils import _
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form


@view_config(route_name="contact", renderer="contact.mako")
def contact(context, request):
    return {"sidebar_data": {}}


@view_config(route_name="support", renderer="contact.mako")
def contact(context, request):
    return {"sidebar_data": {}}


def includeme(config):
    config.add_route("contact", "/@@contact")
    config.add_route("support", "/@@contact_support")
