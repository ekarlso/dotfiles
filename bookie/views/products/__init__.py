def includeme(config):
    config.add_route("category_add", "/@{group}/category/add")
    config.add_route("category_manage", "/@{group}/category/{resource_id}/edit")
    config.add_route("category_overview", "/@{group}/category")

    config.add_route("entity_add", "/g,{group}/entity/add")
    config.add_route("entity_bulk_add", "/g,{group}/entity/bulk_add")
    config.add_route("entity_manage", "/g,{group}/entity/{id}/manage")
    config.add_route("entity_view", "/g,{group}/entity/{id}/view")
    config.add_route("entity_overview", "/g,{group}/entity")
