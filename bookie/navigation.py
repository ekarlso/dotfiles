from bookie.utils import _


def nav_top(context, request):
    data = {"check": request.user, "children": [
        {"value": "Home", "check": request.group,
            "view": "retailer_home", "view_kw": {"group": request.group}},
        {"value": "Booking", "check": request.group,
            "view": "booking_overview", "view_kw": {"group": request.group}}]}
    return "navigation", data


def drop_companies(context, request):
    children = []
    children.append({"value": _("Contact a group"), "icon": "message",
        "view": "contact"})
    for g in request.user.retailers:
        children.append(
            {"value": g.group_name, "icon": "group",
                "view": "retailer_home", "view_kw": {"group": g.group_name}})
    return "dropdown_button", {"value": _("Companies"), "icon": "dashboard", "children": children}


def drop_user(context, request):
    user_value = request.user.first_name + " - " + request.user.user_name \
        if request.user.first_name else request.user.user_name
    return "dropdown", {
        "value": user_value, "icon": "user", "children": [
            {"value": _("Preferences"), "icon": "user", "view": "user_account"},
            {"value": _("Reset password"), "icon": "wrench",
                "view": "reset_password"},
            {"value": _("Logout"), "icon": "warning-sign", "view": "logout"}]}
