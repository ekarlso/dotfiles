% if menu.is_showable:
<a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
    % for i in menu:
        % if i.is_showable:
        <span class="icon-bar"></span>
        % endif
    % endfor
</a>
<div class="nav-collapse">
    <ul class="nav">
    % for i in menu:
        % if i.is_showable:
        <li${' class="%s"' % i.cls if i.cls else ''}>
            <a href="${i.url}">${i.icon_html}${i.value}</a>
        </li>
        % endif
    % endfor
    </ul>
</div><!-- nav-collapse -->
% endif
