<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="">
<meta name="author" content="">

<title><%block name="head_title">${api.page_title}</%block></title>


% for url in environment["css"].urls():
    <link rel="stylesheet" type="text/css" href="${url}" />
% endfor
<link rel="stylesheet" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.18/themes/base/jquery-ui.css">

<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.8.1/jquery.min.js"></script>
<script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.18/jquery-ui.min.js"></script>

<script type="text/javascript" src="http://code.angularjs.org/1.0.1/angular-1.0.1.min.js"></script>
<script type="text/javascript" src="http://cdn.jsdelivr.net/angularjs/1.0.1/angular-resource-1.0.1.min.js"></script>
<script type="text/javascript" src="http://cdn.jsdelivr.net/angularjs/1.0.1/angular-bootstrap-1.0.1.min.js"></script>
<script type="text/javascript" src="http://raw.github.com/angular-ui/angular-ui/master/build/angular-ui.js"></script>

% for script in environment["js"].urls():
    <script type="text/javascript" src="${script}"></script>
% endfor

<!--more tal:omit-tag="" metal:define-slot="head-more"></more-->

<!-- Fav icons -->
<!--link rel="shortcut icon" href="${request.static_url('bookie:static/favicon.ico')}" /-->

<style type="text/css">
    body {
        padding-top: 60px;
        padding-bottom: 40px;
    }
</style>

<!-- Le HTML5 shim, for IE6-8 support of HTML5 elements -->
<!--[if lt IE 9]>
    <script src="http://html5shim.googlecode.com/svn/trunk/html5.js"></script>
<![endif]-->

</head>
