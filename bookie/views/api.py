from cornice import Service
from cornice.resource import resource, view

from bookie.ext_json import json
from bookie.models import models as m
from bookie.views.search import search_options


class APIBase(object):
    entity = None

    def __init__(self, request):
        self.request = request
        self.id_ = request.matchdict.get("id", None)

    @staticmethod
    def render_collection(collection):
        return {"data": [obj.to_dict(deep=dict(metadata={})) \
                for obj in collection]}

    @view(permission="view")
    def collection_get(self):
        opts = search_options(self.request)
        opts["filter_by"]["retailer"] = self.request.group
        collection = self.entity.search(**opts)
        return self.render_collection(collection)

    @view(permission="view")
    def get(self):
        obj = self.entity.get_by(id=self.id_, retailer=self.request.group)
        return obj.to_dict()

    def delete(self):
        obj = self.entity.get_by(id=self.id_, retailer=self.request.group)
        obj.delete()
        return {}




@resource(collection_path="/api/{group}/category",
        path="/api/{group}/category/{id}", permission="view")
class CategoryAPI(APIBase):
    entity = m.Category

    def get(self):
        obj = self.entity.get_by(
                resource_id=self.id_,
                owner_group_id=self.request.group.id)
        return obj.to_dict()

    def collection_get(self):
        query = m.Category.query.filter(
                m.Resource.owner_group_id==self.request.group.id)
        db_data = m.Category.search(query=query)
        return [row.to_dict(exclude=["updated_at"]) for row in db_data]


@resource(collection_path="/api/{group}/entity",
        path="/api/{group}/entity/{id}")
class EntityAPI(APIBase):
    entity = m.Entity


def includeme(config):
    config.add_renderer("simplejson", json)
