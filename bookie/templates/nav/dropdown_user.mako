% if request.user:
<div class="btn-group pull-right">
    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
        <i class="icon-user"></i>${request.user.first_name} / ${request.user.user_name}
        <span class="caret"></span>
    </a>
    <ul class="dropdown-menu">
        <li><a href="/@@prefs">Preferences</a></li>
        <li class="divider"></li>
        <li><a href="/@@logout">Sign Out</a></li>
    </ul>
</div><!-- User dropdown -->
% endif
