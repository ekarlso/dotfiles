<!DOCTYPE html>
<html lang="en" ng-app="bookie">
<%include file="head.mako"/>

<body>
<%block name="navbar_wrapper">
<div class="navbar navbar-fixed-top">
    <div class="navbar-inner">
        <div class="container-fluid">
            <a class="brand" href="!#/">Bookie BETA</a>

            <%block name="navbar_global">
            <div ng-controller="AccountNavCtrl">
                <a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse" ng-href="">
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </a>
                <div class="nav-collapse">
                    <ul class="nav">
                        <!-- Navbar start -->
                        <li><a href="!#/{{account.uuid}}/home">Home</a></li>
                        <li><a href="!#/{{account.uuid}}/entity">Entity</a></li>
                        <li class="dropdown">
                            <a ng-nref="" class="dropdown-toggle" data-toggle="dropdown">Settings<b class="caret"></b></a>
                            <ul class="dropdown-menu">
                                <li><a ng-href="#{{account.uuid}}/category">Category</a></li>
                                <li><a ng-href="#{{account.uuid}}/location">Location</a></li>
                            </ul>
                        </li>
                        <li><a href="#/about">About</a></li>
                    </ul>
                    <!-- Navbar end -->
                </div>
            </div>
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
