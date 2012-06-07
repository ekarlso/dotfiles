
<%def name="get_url(path)">
    <%
        return request.static_url("bookie:" + path)
    %>
</%def>


<%def name="mk_styles(styles)">
    % for style in styles:
        <link rel="stylesheet" type="text/css" href="${get_url(style)}" />
    % endfor
</%def>


<%def name="mk_scripts(scripts)">
    % for script in scripts:
        <script src="${get_url(script)}"></script>
    % endfor
</%def>


