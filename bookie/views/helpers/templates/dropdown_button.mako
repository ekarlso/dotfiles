<%doc>
The top item has the menu value typically.
In the dropdown case we use it to set the value of the dropdown caret button
</%doc>
% if menu.is_showable:
<div class="btn-group pull-right">
    <a class="btn" href="${menu.tree.url}">${menu.tree.icon_html}${menu.tree.value}</a>
    <a class="btn dropdown-toggle" data-toggle="dropdown">
        <span class="caret"></span>
    </a>
    <ul class="dropdown-menu">
        % for i in menu:
            % if i.is_showable:
            <% li_cls = ' class="%s"' % i.cls if i.cls else ''%>
            <li${li_cls}>
            % if i.url:
                <a href="${i.url}">
                    ${i.icon_html}${i.value}
                </a>
                % endif
            </li>
            % endif
        % endfor
    </ul>
</div>
% endif
