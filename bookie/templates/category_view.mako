<%inherit file="/base.mako"/>

<%block name="content">
    <div class="row-fluid">
        <div class="span3">
            <em>Category Info</em>
            <table>
                <tr>
                    <td>Name</td><td>${obj.resource_name}</td>
                </tr>
                <tr>
                    <td>Description</td><td>${obj.description}</td>
                </tr>
            </table>
        </div>
        <div class="span6">
        </div>
    </div>
</%block>
