<%inherit file="/base.mako"/>

<%block name="content">
<div class="row-fluid">
    <table class="table table-striped">
        ${form["form"]|n}
    </table>
</div>
</%block>
