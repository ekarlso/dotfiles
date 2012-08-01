<%inherit file="base.mako"/>

<%block name="content">
<em>From</em>: ${obj.sender}<br/>
% if not obj.receivers:
    To: ${obj.receivers}
% endif
<br/>


<em>Content:</em><br/>
<blockquote>
    ${obj.content}
</blockquote>
</%block>
