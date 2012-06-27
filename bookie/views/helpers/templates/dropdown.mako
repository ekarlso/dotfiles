<div class="btn-group pull-right">
    <%doc>
    The top item has the menu value typically.
    In the dropdown case we use it to set the value of the dropdown caret button
    </%doc>
    <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
        <i class="icon-user"></i>${menu.tree.value}
        <span class="caret"></span>
    </a>
    <ul class="dropdown-menu">
        % for i in menu:
            <% li_cls = ' class="%s"' % i.cls if i.cls else ''%>
            <li${li_cls}>
            % if i.url:
                <a href="${i.url}">
                    ${i.icon_html}${i.value}
                </a>
                % endif
            </li>
        % endfor
    </ul>
</div>
