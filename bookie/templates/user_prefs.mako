<%inherit file="base.mako"/>

<%block name="left">
<div class="span2">
    <div class="well sidebar-nav">
        <ul class="nav nav-list">
            <li class="nav-header">My Settings</li>
            <li class="active"><a href="@@prefs" >Preferences</a></li>
        </ul>
    </div>
</div>
</%block>

<%block name="content">
    <div class="span9">
        ${form|n}
    </div>
</%block>
