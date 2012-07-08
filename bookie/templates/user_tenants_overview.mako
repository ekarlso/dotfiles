<%inherit file="/base.mako"/>

<%block name="content">
<div class="row-fluid">
    % if not request.user.retailers:
        <p>You do not have any tenants</p>
    % else:
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
            % for tenant in request.user.retailers:
                <td>${tenant}</td>
                <td>${api.name_to_camel(tenant.group_type)}</td>
                <td><a class="btn" href="${api.route_url('user_tenant_setter', _query={'name': tenant.group_name})}">Set to current</a></td>
            % endfor
            </tr>
        </tbody>
    </table>
    % endif
</div>
</%block>
