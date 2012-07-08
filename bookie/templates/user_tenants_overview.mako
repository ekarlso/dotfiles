<%inherit file="/base.mako"/>

<%block name="content">
<div class="row-fluid">
% if not request.user.retailers:
    <p>You do not have any tenants</p>
% else:
    <p>${request.user.current_group}
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
            % for group in request.user.retailers:
                <td>${group}</td>
                <td>${api.name_to_camel(group.group_type)}</td>
                <td>
                    <% url = api.route_url('user_tenant_setter', _query={'name': group.group_name}) %>
                    <a class="btn disabled" href="${url}">Set to current</a>
                </td>
            % endfor
            </tr>
        </tbody>
    </table>
% endif
</div>
<script type="text/javascript">
    $(document).ready(function() {
        $("a.disabled").click(function(event) {
            event.preventDefault();
        });
    });
</script>
</%block>

