<div class="navbar navbar-fixed-top">
<div class="navbar-inner">
<div class="container-fluid">

<a class="brand" href="/">Bookie BETA</a>

<%
#data = request.matchdict.copy()

menu_nav = {"check": request.user, "children": [
    {"value": "Home", "view_name": "index"},
    {"value": "Dashboard", "check": request.group,
        "view_name": "retailer_home", "view_kw": {"group": request.group}},
    {"value": "Booking", "check": request.group,
        "view_name": "booking_overview", "view_kw": {"group": request.group}}]}
%>
${api.nav(menu_nav)}

<%doc>
Menu for when a user is authed
</%doc>
<%
if request.user:
    children = []
    children.append({"value": _("Contact a group"), "icon": "user",
        "view_name": "contact"})
    for g in request.user.retailers:
        children.append(
            {"value": g.group_name, "view_name": "retailer_home", 
                "view_kw": {"group": g.group_name}})
    drop_companies = {"value": _("Companies"), "children": children}

    user_value = request.user.first_name + " - " + request.user.user_name
    drop_user = {
        "value": user_value, "icon": "user", "children": [
            {"value": _("Preferences"), "icon": "user", "view_name": "user_prefs"},
            {"value": _("Reset password"), "icon": "wrench", 
                "view_name": "reset_password"},
            {"value": _("Logout"), "icon": "warning-sign", "view_name": "logout"}]}
%>
% if request.user:
${api.dropdown(drop_user)}
${api.dropdown_button(drop_companies)}
% endif

</div><!-- container -->
</div><!-- navbar-inner-->
</div><!-- navbar -->
