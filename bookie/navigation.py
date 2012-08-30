import logging

from bookie.utils import _

LOG = logging.getLogger(__name__)


def drop_user(context, request):
    user_value = request.user.first_name + " - " + request.user.user_name \
        if request.user.first_name else request.user.user_name
    return "dropdown", {
        "value": user_value, "icon": "user", "children": [
            {"value": _("Preferences"), "icon": "user", "route": "user_account"},
            #{"value": _("Reset password"), "icon": "wrench",
            #    "route": "reset_password"},
            {"value": _("Messages"), "icon": "envelope",
                "route": "message_overview"},
            {"value": _("Logout"), "icon": "warning-sign", "route": "logout"}]}
