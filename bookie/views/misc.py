import logging
import re

import colander
import deform
import deform_bootstrap.widget as db_widget
import sqlalchemy
import sqlalchemy.orm

import pyramid.httpexceptions as exceptions
from pyramid.threadlocal import get_current_request
from pyramid.view import view_config

from .. import models
from ..utils import _
from . import helpers, search


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
            if user.id == request.user.id:
                continue
            recipients["u:" + user.user_name] = user.display_name
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


def recipients_validate(node, values):
    possibles = possible_recipients(get_current_request())
    if not values:
        raise colander.Invalid(node, _("No recipients"))

    invalid = []
    for value in values:
        if not value in possibles:
            invalid.append(value)
    if invalid:
        raise colander.Invalid(node, "Invalid recipient %s" % ", ".join(invalid))


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
    links = []
    links.append({"value": _("New"), "route": "message_send"})
    links.append({"value": "divider"})
    links.append({"value": _("Inbox"), "route": "message_overview"})
    links.append({"value": _("Sent"), "route": "message_overview",
        "url_kw": dict(_query=dict(show="sent"))})
    return [{"value": _("Navigation"), "children": links}]


@view_config(route_name="contact", renderer="misc/contact.mako")
def contact(context, request):
    return {"sidebar_data": {}}


@view_config(route_name="support", renderer="misc/support.mako")
def support(context, request):
    return {"sidebar_data": {}}


class Recipients(colander.SequenceSchema):
    string = colander.SchemaNode(
            colander.String())


class MessageSchema(colander.Schema):
    recipients = Recipients(
            widget=db_widget.ChosenMultipleWidget(min_length=1, size=100),
            title=_("Recipients"),
            validator=recipients_validate)
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
        # NOTE: Determine whats groups and users
        users = set()
        groups = set()
        for string, type_ in map(recipient_resolve, appstruct["recipients"]):
            if type_ == "user":
                users.add(string)
            elif type_ == "group":
                groups.add(string)

        # NOTE: Translate user_name into id
        db_users = [u.id for u in models.User.query.filter(
            models.User.user_name.in_(users))]

        assert(len(users) == len(db_users))
        user_ids = set(db_users)

        # NOTE: Lets only care for getting the users from groups if there
        # actually are groups...
        if len(groups) != 0:
            # NOTE: Use joinedload to not use multiple queries.
            query = models.Account.query.options(
                    sqlalchemy.orm.joinedload("users"))
            query = query.filter(models.Group.uuid.in_(groups))
            for group in query:
                for user in group.users:
                    user_ids.add(user.id)

        if self.request.user.id in user_ids:
            user_ids.remove(self.request.user.id)

        message = models.Message(
                content=appstruct["message"],
                sender=self.request.user)
        for id_ in user_ids:
            models.MessageAssociation(user_id=id_, message=message)
        message.save()

        self.request.session.flash("Your message was delivered to %d users!" % \
                len(user_ids))
        location = self.request.route_url("message_overview",
                _query={"show": "sent"})
        return exceptions.HTTPFound(location=location)


@view_config(route_name="message_send", permission="view",
        renderer="message_send.mako")
def message_send(context, request):
    return helpers.mk_form(MessageForm, context, request,
            extra={"sidebar_data": message_links(request)})


@view_config(route_name="message_overview", permission="view",
        renderer="grid.mako")
def message_overview(context, request):
    params = request.params.copy()
    show = params.pop("show", "inbox")

    # NOTE: Let us use search_opts
    search_opts = search.search_options(params)

    cols = ["id", "created_at"]
    if show == "inbox":
        filters = []
        filters.append(models.Message.id==models.MessageAssociation.message_id)
        filters.append(models.MessageAssociation.user==request.user)
        search_opts["filters"] = filters
        cols.append("sender")
    elif show == "sent":
        search_opts["filters"] = [models.Message.sender==request.user]
        cols.append("receivers_string")
    cols.append("short")

    # NOTE: Add in User model.
    messages = models.Message.search(**search_opts)

    grid = helpers.PyramidGrid(messages, cols)
    # NOTE: This (id) becomes a buttoned link
    grid.labels["id"] = ""
    grid.labels["created_at"] = _("Time")
    grid.labels["receivers_string"] = _("Receivers")
    grid.labels["short"] = _("Short contents")

    grid.column_formats["id"] = lambda cn, i, item: helpers.column_link(
        request, "View", "message_view",
        url_kw=dict(came_from=request.current_route_url(), id=item.id),
        class_="btn btn-primary")

    return {"sidebar_data": message_links(request),
            "page_title": "Messages", "sub_title": show.title(), "grid": grid}


@view_config(route_name="message_view", permission="view",
        renderer="message_view.mako")
def message_view(context, request):
    msg_id = request.matchdict["id"]
    obj = models.Message.get_by(id=msg_id)
    if obj.sender == request.user or obj.user_is_recipient(request.user):
        pass
    else:
        raise exceptions.HTTPNotFound
    return {"sidebar_data": message_actions(request), "obj": obj}


def message_delete(context, request):
    msg_id = [request.params.get("id", None)]


def includeme(config):
    config.add_route("contact", "/contact")
    config.add_route("support", "/support")
    config.add_route("message_send", "/message/send")
    config.add_route("message_view", "/message/{id}")
    config.add_route("message_overview", "/message")
