import itertools

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

        self.title = title
        self.url = url
        self.icon = icon

        self.parent = parent

        self.children = [self.create(context, request, parent=self, **i) for i in children]

    @classmethod
    def create(cls, context, request, **data):
        return cls(context, request, **data)

    def is_active(self, url):
        """
        Is this the active menu item?
        """
        return self.url == url and "active" or ""
