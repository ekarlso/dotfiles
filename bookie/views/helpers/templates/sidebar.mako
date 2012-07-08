% if menu.is_showable:
<div class="well sidebar-nav">
    <ul class="nav nav-list">
    % for item in menu:
        % if item.is_showable:
        <%
            if item.is_parent:
                li_cls = ' class="%s"' % (item.cls + " nav-header")
            else:
                li_cls = ' class="%s"' % item.cls if item.cls else ''
        %>
        <li${li_cls}>
            % if item.is_parent:
            ${item.value}
            % else:
            <a href="${item.url}">${item.icon_html}${item.value}</a>
            % endif
        </li>
        % endif
    % endfor
    </ul>
</div>
% endif
