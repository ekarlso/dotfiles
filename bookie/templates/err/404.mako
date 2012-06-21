<%inherit file="/base.mako"/>

<%block name="heading_wrapper"/>
<%block name="content">
<div class="span6 alert">
    <div class="alert">
        <div class="page-header">
            <h1>Ooops... Page not found!</h1>
            <h2 tal:content="first_header | default"></h2>
        </div>
        <div>
            It looks like you have requested a resource which I can't find for you.

            If you think it should exist please contact ${api.utils.create_anchor('support', 'support_contact')}
        </div>
    </div>
</div>
</%block>
