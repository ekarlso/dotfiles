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
    <div class="span9">

    <!-- TODO: make span settable? -->
    <%doc>
        We support 2 different types of heading styles:
            1. The page_header is set and will be the top header of the page
            2. The page_header is set and sub_header is set, page_header is like in 1. but has sub_header underneath
    </%doc>
    <%block name="heading_wrapper">
        <div class="row-fluid">
            <div class="page-header">
                <%block name="page_heading">
                    <h1>${page_title or api.page_title}</h1>
                </%block>

                <%block name="sub_heading">
                    % if sub_title:
                        <h2>${sub_title}</h2>
                    % endif
                </%block>
            </div>
        </div>
    </%block>

    <%doc>
        Place content beneath the content header
        At the moment the content block is left to implement it's own row-fluids / hero-units

        We impose a span[0-9] on the content to limit it's width
    </%doc>
    <%block name="content"/>

    </div>
</%block>
