<div metal:fill-slot="content" id="content">
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
        <table class="stylized">
            <h1 >Users</h1>
            <table tal:replace="structure user_grid"/>
        </table>
    </div>
    <div class="tab-pane" id="add-user-tab">
        <h1 tal:content="user_addform['first_heading']"/>
        <form tal:replace="structure user_addform['form']"/>
    </div>

    <div class="tab-pane" id="list-group-tab">
        <table class="stylized">
            <h1 >Groups</h1>
            <table tal:replace="structure group_grid"/>
        </table>
    </div>
    <div class="tab-pane" id="add-group-tab">
        <h1 tal:content="group_addform['first_heading']"/>
        <form tal:replace="structure group_addform['form']"/>
    </div>
</div>
</div>

</html>
