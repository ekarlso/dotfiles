<%inherit file="/base.mako"/>

<%block name="content">
<div class="row-fluid">
    <div class="span3">
        <em>Vehicle information</em>
        <table clasS="table table-condensed">
            <tr>
                <td>Brand</td><td>${entity.brand}</td>
            </tr>
            <tr>
                <td>Model name</td><td>${entity.model}</td>
            </tr>
            <tr>
                <td>Procuced in</td><td>${entity.produced}</td>
            </tr>
            <tr>
                <td>Identifer</td><td>${entity.identifier}</td>
            </tr>
            <tr>
                <td>Owner</td><td>${entity.retailer}</td>
            </tr>
        </table>
    </div>
    <div class="span6">
        <em>Latest bookings</em>
        <table class="table table-condensed">
            ${b_grid_latest}
        </table>
    </div>
</div>
</%block>
