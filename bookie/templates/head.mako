<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="">
<meta name="author" content="">

<title><%block name="head_title">${api.page_title}</%block></title>


% for url in environment["css"].urls():
    <link rel="stylesheet" type="text/css" href="${url}" />
% endfor

% for script in environment["js"].urls():
    <script type="text/javascript" src="${script}"></script>
% endfor

<!-- 3rd party -->
${api.css_link([
    "deform:static/css/jquery-ui-timepicker-addon.css"
])|n}

${api.script_link([
    "deform:static/scripts/jquery-ui-timepicker-addon.js",
    "deform:static/scripts/jquery.form.js",
    "deform:static/scripts/deform.js",
    "deform_bootstrap:static/deform_bootstrap.js"
])|n}


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
