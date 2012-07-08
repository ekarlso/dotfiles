<%inherit file="/base.mako"/>

<%block name="content">
<div class="row-fluid">
    <p>It doesn't look like you have any tenant set, please choose one:</p>
    <table class="table table-condensed">
        <thead>
            <tr>
                <th>Tenant</th>
                <th>Type</th>
                <th>Activate?</th>
            </tr>
        </thead>
        <tbody>
            <tr>
            % for tenant in request.user.groups:
                <td>${tenant}</td>
                <td>${api.name_to_camel(tenant.group_type)}</td>
                <td><a class="btn" href="${api.route_url('user_tenant_setter', _query={'name': tenant.group_name})}">Set to current</a></td>
            % endfor
            </tr>
        </tbody>
    </table>
</div>
</%block>
