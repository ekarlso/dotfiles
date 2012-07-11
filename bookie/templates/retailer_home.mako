<%inherit file="/base.mako"/>

<%block name="content">
<div class="row-fluid">
    <div class="span5" style="font-align: center;">
        <h2>Quick Tasks</h2>
        <br/>
        ${api.get_nav('actions', data=nav_quick)}
    </div>
    <div class="span5">
        <h2>Messages</h2>
    </div>
</div>
</%block>
