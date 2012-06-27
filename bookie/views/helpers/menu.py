from itertools import chain
import os.path
import re

from mako.template import Template
from mako.lookup import TemplateLookup

from .utils import get_url


STYLE_CLS = [
    "divider"
]


def menu_item(value, view_name, *args, **kw):
    """
    A simple helper for generating out menu dicts
    """
    return {
        "value": value,
        "view_name": view_name,
        "view_args": args,
        "view_kw": kw}


def get_template(template):
    template_dir = os.path.dirname(__file__) + "/templates/"
    lookup = TemplateLookup(directories=[template_dir])
    return lookup.get_template(template)


class MenuItem(object):
    """
    A Basic menu item

    :param context: A context
    :param request: A request

    :param value: The value / text for this menu item
    :param url: The href / url for this menu item
    :param icon: A Icon to prepend to the text

    :param children: A list of children dicts
    :param parent: The parent of this item
    """
    def __init__(self, context, request, parent=None, children=[], value=None,
        url=None, icon=None, view_name=None, view_args=[], view_kw={}):
        self.context, self.request = context, request

        self.parent = parent
        new_children = []
        for child in children:
            if len(child) > 0:
                # NOTE: Skip empty items
                new_children.append(
                    self.__class__(context, request, parent=self, **child))
        self.children = new_children

        self.value = value

        # NOTE: View override url
        if view_name:
            url = get_url(view_name, *view_args, **view_kw)
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

    # TODO: FIX ME
    def levels(self):
        """
        Should return at what level we're at in the menu indent structure
        """
        i = 0
        c = self
        while (getattr(c, "parent", False)):
            c = c.parent
            i += 1

    @property
    def cls(self):
        cls = []
        if not self.value in STYLE_CLS and self.url == self.request.url:
            cls.append("active")
        elif self.value.lower() in STYLE_CLS:
            cls.append(self.value.lower())
        return " ".join(cls)


    @property
    def icon_html(self):
        return '<i class=%s></i>' % self.icon if self.icon else ''

    def __iter__(self):
        return iter(self.children)

    def subitems(self):
        for i in self:
            for ci in i.items():
                yield ci

    def items(self):
        yield self
        for i in self.subitems():
            yield i


class Menu(object):
    """
    A Menu
    """
    template = None
    def __init__(self, context, request, struct):
        self.tree = MenuItem(context, request, **struct)

    def __iter__(self):
        return self.tree.subitems()

    def __html__(self):
        return get_template(self.template).render(menu=self)

    @property
    def top(self):
        return self.tree


class Dropdown(Menu):
    template = "dropdown.mako"


class Sidebar(Menu):
    template = "sidebar.mako"
    def __init__(self, context, request, struct):
        # NOTE: We want a list since we'll get object from beneath the first
        # item of the menu tree in the for i in ... loop
        if type(struct) == list:
            struct = {"children": struct}
        else:
            raise ValueError("Struct should be a list...")
        super(Sidebar, self).__init__(context, request, struct)
