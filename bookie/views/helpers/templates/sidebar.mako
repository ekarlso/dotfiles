<div class="well sidebar-nav">
    <ul class="nav nav-list">
    % for i in menu:
        <%
            if i.is_parent:
                li_cls = ' class="%s"' % (i.cls + " nav-header")
            else:
                li_cls = ' class="%s"' % i.cls if i.cls else ''
        %>
        <li${li_cls}>
            % if i.is_parent:
            ${i.value}
            % else:
            <a href="${i.url}">${i.icon_html}${i.value}</a>
            % endif
        </li>
    % endfor
    </ul>
</div>
