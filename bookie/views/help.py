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

from ..db import models
from ..utils import _
from .helpers import AddFormView, EditFormView, PyramidGrid, mk_form
from .helpers import get_url


@view_config(route_name="support_contact",
            renderer="bookie:templates/help/contact.pt")
def support_contact(context, request):
    return {}


def includeme(config):
    config.add_route("support_contact", "/@@contact")
