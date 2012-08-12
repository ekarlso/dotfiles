import colander
import deform
import pyramid.httpexceptions as exceptions

from .. import models
from ..utils import _
from . import helpers as h, search


"""
This contains user pages
"""


def welcome(context, requests):
    import ipdb
    ipdb.set_trace()


def includeme(config):
    config.add_route("welcome", "/welcome")
