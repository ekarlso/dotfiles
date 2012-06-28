<div class="navbar navbar-fixed-top">
<div class="navbar-inner">
<div class="container-fluid">

<a class="brand" href="/">Bookie BETA</a>
<a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
</a>

<%
# NOTE: Should we move this?
data = request.matchdict.copy()
if not "group" in data:
    data["group"] = "default"

menu_nav = {"children": [
    {"value": "Home", "view_name": "index"}, 
    {"value": "Booking", "view_name": "booking_overview", "view_kw": data}, 
    {"value": "Cars", "view_name": "entity_overview", "view_kw": data}]}
%>
${api.nav(menu_nav)}

<%doc>
Menu for when a user is authed
</%doc>
<%
    if request.user:
        dd_companies = {
            "value": "Companies", "icon": "user", "children": [
                {"value": "Request access to a company",
                "view_name": "group_req_access"}]}
        user_value = request.user.first_name + " - " + request.user.user_name
        dd_user = {
            "value": user_value, "icon": "user", "children": [
                {"value": "Preferences", "view_name": "user_prefs"},
                {"value": "Reset password", "view_name": "reset_password"}]}
%>
% if request.user:
    ${api.dropdown(dd_user)}
    ${api.dropdown(dd_companies)}
% endif

</div><!-- container -->
</div><!-- navbar-inner-->
</div><!-- navbar -->
