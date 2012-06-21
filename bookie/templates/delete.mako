<%inherit file="base.mako"/>

<%block name="content">
<div class="row-fluid">
    <% deleted = request.params.get('do', False) == 'yes' %>
    <div class="page-header">
        % if deleted:
            <h1>Deleted</h1>
        % else:
            <h1>Confirm Deletion</h1>
        % endif
        <h2>${first_heading}</h2>
    </div>

    % if deleted:
        <div>Entity is now deleted.</div>
    % else:
        <div class="alert">
            WARNING:<br/>
            The action you are about to perform is undoable, to proceed click on the Delete button below.<br/><br/>
            <a class="btn btn-danger" id="delete" href="${request.url}?do=yes">Delete</a>
        </div>
    % endif
</div>
</%block>
