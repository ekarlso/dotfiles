<!DOCTYPE html>
<html lang="en">
<%include file="head.mako"/>

<body>
<%block name="navbar_wrapper">
<div class="navbar navbar-fixed-top">
    <div class="navbar-inner">
        <div class="container-fluid">
            <a class="brand" href="/">Bookie BETA</a>

            <%block name="navbar_global">
            ${api.get_nav("nav_top")}
            </%block>

            % if request.user:
            ${api.get_nav("drop_user")}
            % endif
            <%block name="navbar_local"/>
        </div>
    </div>
</div><!-- navbar -->
</%block>

<div class="container-fluid">
    <div class="row-fluid">
        <%block name="left_wrapper"/>
        <%block name="content_wrapper"/>
        <%block name="right_wrapper"/>
    </div>
    <%include file="footer.mako"/>
</div>

</body>
</html>
