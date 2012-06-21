<%inherit file="base-bare.mako"/>

<%doc>A overridable left_wrapper that always provides a sidebar if sidebar_tree is available</%doc>
<%block name="left_wrapper">
    <%block name="left">
        % if navtree:
            <div class="span2">${self.funcs.sidebar(navtree)}</div>
        % endif
    </%block>
</%block>

<%doc>We override the content_wrapper with our setup</%doc>
<%block name="content_wrapper">
    <!-- TODO: make span settable? -->
    <div class="span9">
        <%doc>
            We support 2 different types of heading styles:
                1. The page_header is set and will be the top header of the page
                2. The page_header is set and sub_header is set, page_header is like in 1. but has sub_header underneath
        </%doc>
        <%block name="page_head_wrapper">
            % if page_header:
            <div class="page-header">
                <h1>${page_header}</h1>
                % if sub_header:
                    <h2>${sub_header}</h2>
                % endif
            </div>
            % endif
        </%block>

        <%doc>Place content beneath the content header</%doc>
        <%block name="content">
        </%block>
    </div>
</%block>
