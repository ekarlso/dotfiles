import itertools
import re


def item(**obj):
    if isinstance(data, MenuItem):
        return obj
    else:
        return MenuItem(**obj)


class MenuItem(object):
    """
    A Basic menu item

    :param context: A context
    :param request: A request

    :param title: The title / text for this menu item
    :param url: The href / url for this menu item
    :param icon: A Icon to prepend to the text

    :param parent: The parent of this item
    :param children: This items children
    """
    def __init__(self, context, request, parent=None, children=[], title=None,
            url=None, icon=None):
        self.context = context
        self.request = request

        self.parent = parent
        self.children = [self.create(context, request, parent=self, **i) for i in children]

        self.title = title
        self.url = url
        if icon and not icon.startswith("icon-"):
            icon = "icon-" + icon
        self.icon = icon

    @classmethod
    def create(cls, context, request, **data):
        return cls(context, request, **data)

    @property
    def is_active(self):
        """
        Is this the active menu item?
        """
        return self.request.url == self.url

    def __html__(self):
        html = """<li%s><a href="%s">%s%s</a></li>"""
        icon_html = '<i class=%s></i>' % self.icon if self.icon else ''
        # NOTE: Need to add support for menu header here (sidebar)
        li_cls = []
        if self.is_active:
            li_cls.append("active")
        li_cls = ' class="%s"' % " ".join(li_cls) \
            if len(li_cls) > 0 else ''
        return html % (li_cls, self.url, icon_html, self.title)
