from itertools import chain
import os.path
import re

from mako.template import Template
from mako.lookup import TemplateLookup


def get_template(template):
    template_dir = os.path.dirname(__file__) + "/templates/"
    lookup = TemplateLookup(directories=[template_dir])
    return lookup.get_template(template)


class MenuItem(object):
    """
    A Basic menu item

    :param context: A context
    :param request: A request

    :param title: The title / text for this menu item
    :param url: The href / url for this menu item
    :param icon: A Icon to prepend to the text

    :param children: A list of children dicts
    :param parent: The parent of this item
    """
    def __init__(self, context, request, parent=None, children=[], title=None, url=None, icon=None):
        self.context, self.request = context, request

        self.parent = parent
        self.children = [self.__class__(context, request, parent=self, **i) for i in children]

        self.title, self.url, = title, url
        self.url = url
        if icon and not icon.startswith("icon-"):
            icon = "icon-" + icon
        self.icon = icon

    @property
    def is_active(self):
        """
        Is this the active menu item?
        """
        return self.request.url == self.url

    @property
    def is_parent(self):
        return len(self.children) > 0

    def levels(self):
        i = 0
        c = self
        while (getattr(c, "parent", False)):
            c = c.parent
            i += 1

    def __iter__(self):
        return iter(self.children)

    def items(self):
        yield self
        for item in self:
            for child_item in item.items():
                yield child_item

    def __html__(self):
        return get_template(self.template).render(item=self)
        html = """<li%s><a href="%s">%s%s</a></li>"""
        icon_html = '<i class=%s></i>' % self.icon if self.icon else ''
        # NOTE: Need to add support for menu header here (sidebar)
        li_cls = []
        if self.is_active:
            li_cls.append("active")
        li_cls = ' class="%s"' % " ".join(li_cls) \
            if len(li_cls) > 0 else ''
        return html % (li_cls, self.url, icon_html, self.title)


class Menu(object):
    """
    A Menu
    """
    template = None
    def __init__(self, context, request, struct):
        self.items = MenuItem(context, request, **struct)

    def __iter__(self):
        return self.items.items()

    def __html__(self):
        return get_template(self.template).render(menu=self)


class Dropdown(Menu):
    template = "dropdown.mako"


class Sidebar(Menu):
    template = "sidebar.mako"
