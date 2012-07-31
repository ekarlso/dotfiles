<%inherit file="base.mako"/>

<%block name="content">
From: ${obj.sender}<br/>
To: ${obj.receivers}
<br/>
<br/>


Content:<br/>
<blockquote>
    ${obj.content}
</blockquote>
</%block>
