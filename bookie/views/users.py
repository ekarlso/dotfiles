import re
from urllib import urlencode

import colander
from deform import Button
from deform.widget import AutocompleteInputWidget, CheckedPasswordWidget, \
    CheckboxChoiceWidget, CheckboxChoiceWidget, PasswordWidget
from pyramid.httpexceptions import HTTPFound
from pyramid.exceptions import Forbidden
from pyramid.view import view_config

from ..utils import _
from .form import AddFormView, EditFormView
from .utils import is_root


class UserSchema(colander.Schema):
    user_name = colander.SchemaNode(colander.String())
    email = colander.SchemaNode(colander.String())
    password = colander.SchemaNode(
        colander.String(),
        validator=colander.Length(min=5, max=100),
        widget=CheckedPasswordWidget(length="20"),
        description="Enter password...")
    #country = colander.SchemaNode(
    #    colander.String(),
    #    widget = deform.widget.SelectWidget(values=constants.country_codes()),
    #)


class UserEditFormView(EditFormView):
    @property
    def success_url(self):
        return self.request.url

    def schema_factory(self):
        return UserSchema()


@view_config(route_name="prefs", permission="view", renderer="user_prefs.html")
def preferences(request):
    user = request.user

    form = UserEditFormView(user, request)()
    if request.is_response(form):
        return form

    return {"form": form["form"]}


def includeme(config):
    config.add_route("prefs", "@@prefs")
    pass
