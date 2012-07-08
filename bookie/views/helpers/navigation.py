from itertools import chain
import os.path
import urllib2

from mako.lookup import TemplateLookup

from .utils import get_url


STYLE_CLS = [
    "divider"
]


def menu_item(value, view_name, *args, **kw):
    """
    A simple helper for generating out menu dicts
    """
    data = {
        "value": value,
        "view_name": view_name,
        "view_args": args,
        "view_kw": kw}
    return data


def menu_came_from(request, value="Go Back"):
    came_from = request.params.get("came_from", None)
    return dict(icon="arrow-left", value=value, url=came_from) \
        if came_from else {}


def get_nav_data(request, extra={}):
    """
    Get some navigational data, GPS coordinate like ;)

    :arg request: Mandatory request
    :type request: Request
    :key extra: Extra data to override the defaults
    :type key: dict
    """
    d = request.matchdict.copy()
    d.update(extra)
    return d


def get_template(template):
    template_dir = os.path.dirname(__file__) + "/templates/"
    lookup = TemplateLookup(directories=[template_dir])
    return lookup.get_template(template)


class MenuBase(object):
    def __init__(self, check=True, *args, **kw):
        self.check = check

    @property
    def is_showable(self):
        check = self.check
        if callable(check):
            check = check(self)
        return True if check else False


class MenuItem(MenuBase):
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
    def __init__(self, context, request, parent=None, check=True, children=[], value=None,
        url=None, icon=None, view_name=None, view_args=[], view_kw={}):
        MenuBase.__init__(self, check)
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
        return urllib2.unquote(self.request.url) == urllib2.unquote(self.url)

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
        """
        Return some css classes for this menu item
        """
        cls = []
        if not self.value in STYLE_CLS and (self.url and self.is_active):
            cls.append("active")
        elif self.value and self.value.lower() in STYLE_CLS:
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


class TreeMenu(MenuBase):
    """
    A menu structure structure that has a menu item on top which is used to
    describe the menu itself and children underneath
    """
    template = None
    multiple = False

    def __init__(self, context, request, struct, check=True):
        MenuBase.__init__(self, check)
        if self.multiple:
            if type(struct) != list:
                raise TypeError("Needs to be list")
            struct = {"children": struct}
        self.tree = MenuItem(context, request, **struct)

    def __iter__(self):
        return self.tree.subitems()

    def __html__(self):
        return get_template(self.template).render(menu=self)

    @property
    def top(self):
        return self.tree


class MultiTreeMenu(TreeMenu):
    multiple = True


class Dropdown(TreeMenu):
    template = "dropdown.mako"


class DropdownButton(TreeMenu):
    template = "dropdown_button.mako"


class Navigation(TreeMenu):
    template = "navigation.mako"


class Actions(MultiTreeMenu):
    template = "actions.mako"


class Sidebar(MultiTreeMenu):
    template = "sidebar.mako"
