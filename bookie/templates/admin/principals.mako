<%inherit file="/base.mako"/>

<%block name="content">
<ul class="nav nav-tabs">
    <li class="active">
        <a href="#list-user-tab" data-toggle="tab" >List users</a>
    </li>
    <li>
        <a href="#add-user-tab" data-toggle="tab" >Add user</a>
    </li>
    <li>
        <a href="#list-group-tab" data-toggle="tab" >List groups</a>
    </li>
    <li>
        <a href="#add-group-tab" data-toggle="tab" >Add group</a>
    </li>
</ul>

<div class="tab-content">
    <div class="tab-pane active" id="list-user-tab">
        <table class="table table-condensed">
            <h1 >Users</h1>
            ${user_grid}
        </table>
    </div>
    <div class="tab-pane" id="add-user-tab">
        <h1>${user_addform['sub_title']}</h1>
        ${user_addform["form"]|n}
    </div>

    <div class="tab-pane" id="list-group-tab">
        <table class="table table-condensed">
            <h1 >Groups</h1>
            ${group_grid}
        </table>
    </div>
    <div class="tab-pane" id="add-group-tab">
        <h1>${group_addform['sub_title']}</h1>
        ${group_addform["form"]|n}
    </div>
</div>
</%block>
