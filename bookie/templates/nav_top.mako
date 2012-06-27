<div class="navbar navbar-fixed-top">
<div class="navbar-inner">
<div class="container-fluid">

<a class="brand" href="/">Bookie BETA</a>
<a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
    <span class="icon-bar"></span>
</a>
<div class="nav-collapse">
    <ul class="nav">
        <li class=""><a href="/">Home</a></li>
        <li class=""><a href="/booking">Booking</a></li>
        <li class=""><a href="/entity/car">Cars</a></li>
    </ul>
</div><!-- nav-collapse -->

<%
    dd_companies = {"value": "Companies", "icon": "user", "children": [
            {"value": "Request access to a company",
            "url": "@@companies/request_access"}]}
    user_value = request.user.first_name + " - " + request.user.user_name
    dd_user = {"value": user_title, "icon": "user", "children": [
            {"value": "Preferences", "url": "@@prefs"}]}
    if request.user:
        api.dropdown(dd_companies)
        api.dropdown(dd_user)
%>

</div><!-- container -->
</div><!-- navbar-inner-->
</div><!-- navbar -->
