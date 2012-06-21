<%def name="navlist(navtree)">
    <ul class="nav nav-list">
    % for item in navtree:
        <li class="nav-header">${item["title"]}</li>

        % for child in item.get("children", []):
            % if "spacer" in child:
                <br/>
            % else: 
                <li class="${request.current_route_url() == child['url'] and 'active' or ''}"><a href="${child['url']}">${child['title']}</a></li>
            % endif
        % endfor
    % endfor
    </ul>
</%def>

<%def name="sidebar(navtree)">
    <div class="well sidebar-nav">${navlist(navtree)}</div>
</%def>
