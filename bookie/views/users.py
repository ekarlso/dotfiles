import re
from urllib import urlencode

from deform import Button
from deform.widget import AutocompleteInputWidget
from deform.widget import CheckedPasswordWidget
from deform.widget import CheckboxChoiceWidget
from deform.widget import SequenceWidget
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import Forbidden
from pyramid.view import view_config

from ..utils import _
from .utils import is_root


@view_config(route_name="prefs", renderer="user_prefs.html")
def preferences(request):
    return {}


def includeme(config):
    config.add_route("prefs", "@@prefs")
    pass
