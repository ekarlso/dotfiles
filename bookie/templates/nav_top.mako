<div class="navbar navbar-fixed-top">
<div class="navbar-inner">
<div class="container-fluid">

<a class="brand" href="/">Bookie BETA</a>

${api.get_nav("nav_top")}

<%doc>
Menu for when a user is authed

NOTE: This should maybe be moved to a .py file? :p
</%doc>
% if request.user:
${api.get_nav("drop_user")}
% if request.user.retailers:
${api.get_nav("drop_companies")}
% endif
% endif


</div><!-- container -->
</div><!-- navbar-inner-->
</div><!-- navbar -->
