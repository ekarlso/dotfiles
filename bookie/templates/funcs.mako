<%def name="nav_list(nav_items)">
    % for item in nav_items:
        % if not item or len(item) == 0:
            continue
        % else:
            ${nav_render(item)}
        % endif
    % endfor
</%def>

<%doc>Handle a item in a menu</%doc>
<%def name="nav_render(item)">
    % if "children" in item:
        % if "title" in item:
            <li class="nav-header">${item["title"]}</li>
        % endif

        ${nav_list(item.get("children"))}
    % elif type(item) == dict:
        ${nav_dict(item)}
    % endif
</%def>

<%def name="nav_dict(item)">
    <li class="${request.current_route_url() == item['url'] and 'active' or ''}">
        <a href="${item['url']}">
        <%
            icon = item.get("icon")
            if icon and not icon.startswith("icon-"):
                icon = "icon-" + icon
        %>
        % if icon:
            <i class="${icon}"></i>
        % endif
        ${item['title']}
        </a>
    </li>
</%def>

<%def name="sidebar(nav_items)">
    <div class="well sidebar-nav">
        <ul class="nav nav-list">${nav_list(nav_items)}</ul>
    </div>
</%def>
