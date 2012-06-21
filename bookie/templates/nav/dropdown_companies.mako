% if request.user:
<div class="btn-group pull-right">
    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
        <i class="icon-user"></i>Companies
        <span class="caret"></span>
    </a>
    <ul class="dropdown-menu">
        <li><a href="/@@companies/req_access">Request access to a company</a></li>
        <li class="divider"></li>
    </ul>
</div><!-- User dropdown -->
% endif
