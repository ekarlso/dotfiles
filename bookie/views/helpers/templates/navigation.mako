<a class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
    % for i in menu:
        <span class="icon-bar"></span>
    % endfor
</a>
<div class="nav-collapse">
    <ul class="nav">
    % for i in menu:
        <li${'class="%s"' % i.cls if i.cls else ''}>
            <a href="${i.url}">${i.icon_html}${i.value}</a>
        </li>
    % endfor
    </ul>
</div><!-- nav-collapse -->
