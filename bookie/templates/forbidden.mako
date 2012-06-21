<%inherit file="base.mako"/>

<%doc>Clear page_header here</%doc>
<%block name="heading_wrapper"/>

<%block name="content">
<div class="row-fluid alert">
    <div class="page-header">
        <h1>Ooops... Unauthorized access attempted.</h1>
    </div>
    <div>
        You are not allowed to view the request page.
    </div>
</div>
</%block>
