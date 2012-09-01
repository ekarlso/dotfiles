from bookie.utils import _
from .. import helpers as h

def get_links(request, obj=None):
    data = h.get_nav_data(request)

    entity_links = []
    entity_links.append(h.menu_came_from(request))
    entity_links.append(h.menu_item(_("Overview"), "entity_overview", **data))
    entity_links.append(h.menu_item(_("Add"), "entity_add", **data))
    entity_links.append(h.menu_item(_("Bulk add"), "entity_bulk_add", **data))

    category_links = []
    category_links.append(h.menu_item(_("Overview"), "category_overview", **data))
    category_links.append(h.menu_item(_("Add"), "category_add", **data))

    menu = [
            {"value": _("Entity") + " " + _("management"), "children": entity_links},
            {"value": _("Category") + " " + _("management"), "children": category_links}]

    return menu


def includeme(config):
    config.add_route("category_add", "/g,{group}/category/add")
    config.add_route("category_manage", "/g,{group}/category/{resource_id}/manage")
    config.add_route("category_overview", "/g,{group}/category")

    config.add_route("entity_add", "/g,{group}/entity/add")
    config.add_route("entity_bulk_add", "/g,{group}/entity/bulk_add")
    config.add_route("entity_manage", "/g,{group}/entity/{id}/manage")
    config.add_route("entity_view", "/g,{group}/entity/{id}/view")
    config.add_route("entity_overview", "/g,{group}/entity")
