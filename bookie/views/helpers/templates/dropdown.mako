% if menu.is_showable:
<div class="btn-group pull-right">
    <%doc>
    The top item has the menu value typically.
    In the dropdown case we use it to set the value of the dropdown caret button
    </%doc>
    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
        ${menu.tree.icon_html}${menu.tree.value}
        <span class="caret"></span>
    </a>
    <ul class="dropdown-menu">
        % for item in menu:
            % if item.is_showable:
            <% li_cls = ' class="%s"' % item.cls if item.cls else ''%>
            <li${li_cls}>
            % if item.url:
                <a href="${item.url}">
                    ${item.icon_html}${item.value}
                </a>
                % endif
            </li>
            % endif
        % endfor
    </ul>
</div>
% endif
