<%def name="navlist(navtree)">
    <ul class="nav nav-list">
    % for item in navtree:
        <li class="nav-header">${item["title"]}</li>
        % for child in item.get("children", []):
            % if child == "spacer":
                <br/>
            % else: 
                ${navitem(child)}
            % endif
        % endfor
    % endfor
    </ul>
</%def>

<%doc>Handle a item in a menu</%doc>
<%def name="navitem(item)">
    <li class="${request.current_route_url() == item['url'] and 'active' or ''}">
        <a href="${item['url']}">
            <% 
                icon = item.get("icon")
                if icon and not icon.startswith("icon-"):
                    icon = "icon-" + icon
                # <insert default icon handling here?>
            %>
            % if icon:
                <i class="${icon}"></i>
            % endif
            ${item['title']}
        </a>
    </li>
</%def>

<%def name="sidebar(navtree)">
    <div class="well sidebar-nav">${navlist(navtree)}</div>
</%def>
