from cornice import Service
from cornice.resource import resource, view
from pyramid import httpexceptions as exceptions
from pyramid.view import view_config

from bookie.ext_json import json
from bookie.models import models as m
from bookie.views.search import search_options


class APIBase(object):
    entity = None

    def __init__(self, request):
        self.request = request

        # NOTE: If we're hitting an ID
        id_ = request.matchdict.get("id", None)
        if id_ and id_.isdigit():
            id_ = int(id_)
        self.id_ = id_

    def render_collection(self, collection):
        """
        Do obj.serialize() on a collection
        """
        return [obj.serialize() for obj in collection]

    @property
    def is_owned(self):
        """
        Is the self.entity owned by a account?
        """
        return hasattr(self.entity, "account")

    def filter(self):
        """
        Adds filters
        """
        filters = []
        if self.is_owned:
            filters.append(self.entity.account == self.request.account)
        return self.entity.query.filter(*filters)

    def get_id(self):
        """
        Help support using both integer id's and uuid
        """
        query = self.filter()
        return self.entity.get_by(query=query, filter_by=dict(id=self.id_))

    @view(permission="view")
    def get(self):
        obj = self.get_id()
        if not obj:
            raise exceptions.HTTPNotFound
        return obj.serialize()

    @view(permission="view")
    def collection_get(self):
        opts = search_options(self.request)
        query = self.filter()
        collection = self.entity.search(query=query, **opts)
        return self.render_collection(collection)

    def post(self):
        import ipdb
        ipdb.set_trace()

    def delete(self):
        obj = self.entity.get_by(id=self.id_, account=self.request.account)
        obj.delete()
        return {}


def require_account(request):
    if not request.account:
        request.errors.add("account", "required",
                "Missing account in request or default not set")


@resource(collection_path="/user/account", path="/user/account/{id}",
        permission="view")
class AccountAPI(APIBase):
    entity = m.Account

    def get_id(self):
        return self.request.user.get_group(self.id_)

    def collection_get(self):
        """
        This gives you a users accounts
        """
        user = self.request.user
        collection = user.accounts
        # NOTE: If current is not set and the user has only 1 account we switch
        # to it
        return self.render_collection(collection)


@resource(collection_path="/{account}/category", path="/{account}/category/{id}",
        permission="view", validators=require_account)
class CategoryAPI(APIBase):
    entity = m.Category

    def get(self):
        obj = self.entity.get_by(
                resource_id=self.id_,
                owner_group_id=self.request.account.id)
        return obj.to_dict()

    def collection_get(self):
        query = m.Category.query.filter(
                m.Resource.owner_group_id==self.request.account.id)
        collection = m.Category.search(query=query)
        return [row.to_dict(exclude=["updated_at"]) for row in collection]


@resource(collection_path="/{account}/customer", path="/{accounet}/customer/{id}",
        permission="view", validators=[require_account])
class CustomerAPI(APIBase):
    entity = m.Customer


@resource(collection_path="/{account}/entity", path="/{account}/entity/{id}",
        permission="view", validators=require_account)
class EntityAPI(APIBase):
    entity = m.Entity


@resource(collection_path="/{account}/location", path="/{account}/location/{id}",
        permission="view", validators=require_account)
class LocationAPI(APIBase):
    entity = m.Location


@view_config(route_name="category_tree", permission="view", renderer="simple_json")
def category_tree(request):
    """
    Get's a category tree
    """
    top_nodes = m.Category.get_root_nodes(
            filters=[m.Category.owner_group_id==request.account.id])
    tree = [n.subtree_deeper(n.resource_id) for n in top_nodes]



def includeme(config):
    config.add_renderer("simplejson", json)
    config.add_route("category_tree", "{account}/category/tree")
