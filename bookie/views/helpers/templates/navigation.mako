% if menu.is_showable:
<a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
    % for item in menu:
        % if item.is_showable:
        <span class="icon-bar"></span>
        % endif
    % endfor
</a>
<div class="nav-collapse">
    <ul class="nav">
    % for item in menu:
        % if item.is_showable:
        <li${' class="%s"' % item.cls if item.cls else ''}>
            <a href="${item.url}">${item.icon_html}${item.value}</a>
        </li>
        % endif
    % endfor
    </ul>
</div><!-- nav-collapse -->
% endif
