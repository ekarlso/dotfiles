import logging
import re

import colander
import deform
import deform_bootstrap.widget as db_widget
import sqlalchemy
import sqlalchemy.orm

from pyramid.httpexceptions import HTTPFound
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config

from .. import models
from ..utils import _
from . import helpers


def possible_recipients(request):
    """
    Return a dict with all possible recipients

    User: u:username
    Group: g:<uuid>
    """
    recipients = {}
    for group in request.user.groups:
        recipients["g:" + group.uuid] = group.group_name

        for user in group.users:
            recipients["u:" + user.user_name] = user.title
    return recipients


def recipient_resolve(recipient):
    """
    Resolves g:<uuid> to group, <uuid> and u:username user, username

    :param recipient: A recipient string
    """
    match = re.match(r"^(\w+):(\S+)$", recipient)
    type_, string = match.groups()
    type_ = dict(g="group", u="user")[type_]
    return string, type_


def recipient_validate(node, value):
    if not value in possible_recipients(get_current_request()):
        raise colander.Invalid(node, "Invalid recipient %s" % value)


def message_actions(request, obj=None):
    data = helpers.get_nav_data(request)

    links = message_links(request)
    actions = []
    links.append({"value": _("Actions"), "children": actions})
    return links


def message_links(request, obj=None):
    """
    Global message links
    """
    return [{"value": _("Navigation"), "children": [
        {"value": _("Inbox"), "route": "message_overview"},
        {"value": _("Sent"), "route": "message_overview",
            "url_kw": dict(_query=dict(action="sent"))}
        ]}]

@view_config(route_name="contact", renderer="misc/contact.mako")
def contact(context, request):
    return {"sidebar_data": {}}


@view_config(route_name="support", renderer="misc/support.mako")
def support(context, request):
    return {"sidebar_data": {}}


class Recipients(colander.SequenceSchema):
    string = colander.SchemaNode(
            colander.String(),
            validator=recipient_validate)


class MessageSchema(colander.Schema):
    recipients = Recipients(
            widget=db_widget.ChosenMultipleWidget(min_len=1, size=100),
            title=_("Recipients"))
    message = colander.SchemaNode(
            colander.String(),
            validator=colander.Length(max=300),
            widget=deform.widget.TextAreaWidget(rows=10, cols=60),
            title=_("Message text"))


class MessageForm(helpers.AddFormView):
    item_type = _(u"Message")
    buttons = (deform.Button('send_message', _(u'Send message')),
            deform.Button('cancel', _(u'Cancel')))

    def schema_factory(self):
        schema = MessageSchema()
        schema["recipients"].widget.values = possible_recipients(
                self.request).items()
        return schema

    def send_message_success(self, appstruct):
        users = []
        def _append(user):
            """
            Append if the user isnt already in the list of receivers
            """
            if not user in users:
                users.append(user)

        # NOTE: Determine whats groups and users
        groups = []
        for string, type_ in map(recipient_resolve, appstruct["recipients"]):
            _append(string) if type_ == "user" else groups.append(string)

        # NOTE: Translate user_name into id
        db_users = [u.id for u in models.User.query.filter(
            models.User.user_name.in_(users))]

        assert(len(users) == len(db_users))
        user_ids = db_users

        # NOTE: Lets only care for getting the users from groups if there
        # actually are groups...
        if len(groups) != 0:
            # NOTE: Use joinedload to not use multiple queries.
            query = models.Retailer.query.options(
                    sqlalchemy.orm.joinedload("users"))
            for group in groups:
                query = query.filter(models.Retailer.uuid==group)

            for group in query:
                for user in group.users:
                    _append(user.id)

        message = models.Message(
                content=appstruct["message"],
                sender=self.request.user)
        for id_ in user_ids:
            models.MessageAssociation(user_id=id_, message=message)
        message.save()
        return HTTPFound(location=self.request.route_url("message_overview"))


@view_config(route_name="message_send", permission="view",
        renderer="message_send.mako")
def message_send(context, request):
    return helpers.mk_form(MessageForm, context, request)


@view_config(route_name="message_overview", permission="view",
        renderer="grid.mako")
def message_overview(context, request):
    show = request.params.get("action", "inbox")

    cols = ["id", "created_at"]
    if show == "inbox":
        filters = [models.MessageAssociation.user_id==request.user.id]
        cols.append("sender")
    elif show == "sent":
        filters = [models.Message.sender==request.user]
        cols.append("receivers")
    messages = models.Message.search(filters=filters)

    grid = helpers.PyramidGrid(messages, cols)
    grid.labels["id"] = ""
    grid.labels["created_at"] = _("Sent at")

    came_from = {"came_from": request.current_route_url()}

    grid.column_formats["id"] = lambda cn, i, item: helpers.column_link(
        request, "View", "message_view",
        url_kw=dict(came_from.items() + item.to_dict().items()),
        class_="btn btn-primary")

    return {"sidebar_data": message_links(request), "page_title": "Messages", "sub_title": show.title(), "grid": grid}


@view_config(route_name="message_view", permission="view",
        renderer="message_view.mako")
def message_view(context, request):
    msg_id = request.matchdict["id"]
    query = models.Message.query.filter(
            models.MessageAssociation.user_id==request.user.id,
            models.Message.id==msg_id)
    obj = query.one()
    return {"sidebar_data": message_actions(request), "obj": obj}


def message_delete(context, request):
    msg_id = [request.params.get("id", None)]


def includeme(config):
    config.add_route("contact", "/contact")
    config.add_route("support", "/support")
    config.add_route("message_send", "/message/send")
    config.add_route("message_view", "/message/{id}")
    config.add_route("message_overview", "/message")
