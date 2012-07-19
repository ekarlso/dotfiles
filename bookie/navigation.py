from bookie.utils import _


def nav_top(context, request):
    data = {"check": request.user, "children": [
        {"value": "Home", "check": request.group,
            "route": "retailer_home", "url_kw": {"group": request.group}},
        {"value": "Booking", "check": request.group,
            "route": "booking_overview", "url_kw": {"group": request.group}},
        {"value": "Entity", "check": request.group,
            "route": "entity_overview", "url_kw": {"group": request.group}},
        {"value": "Customer", "check": request.group,
            "route": "customer_overview", "url_kw": {"group": request.group}}]}
    return "navigation", data


def drop_companies(context, request):
    children = []
    children.append({"value": _("Contact a group"), "icon": "message",
        "route": "contact"})
    for g in request.user.retailers:
        children.append(
            {"value": g.group_name, "icon": "group",
                "route": "retailer_home", "url_kw": {"group": g.group_name}})
    return "dropdown_button", {"value": _("Companies"), "icon": "dashboard", "children": children}


def drop_user(context, request):
    user_value = request.user.first_name + " - " + request.user.user_name \
        if request.user.first_name else request.user.user_name
    return "dropdown", {
        "value": user_value, "icon": "user", "children": [
            {"value": _("Preferences"), "icon": "user", "route": "user_account"},
            {"value": _("Reset password"), "icon": "wrench",
                "route": "reset_password"},
            {"value": _("Logout"), "icon": "warning-sign", "route": "logout"}]}
