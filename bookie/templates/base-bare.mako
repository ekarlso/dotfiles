<!DOCTYPE html>
<html lang="en">
<%include file="head.mako"/>

<body>
<%include file="nav_top.mako"/>

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
