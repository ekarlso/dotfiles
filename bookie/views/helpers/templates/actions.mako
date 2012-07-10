% if menu.is_showable:
<div class="row-fluid">
% for item in menu:
<div class="span2" style="text-align: center;">
    <a style="text-align: center; font-size: 34px;" href="${item.url}">
        ${item.icon_html}<br />
        <span style="font-size: 10px;">${item.value}</span>
    </a>
</div>
% endfor
</div>
% endif
