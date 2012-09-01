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

    def filter(self, deleted=False):
        """
        Adds filters
        """
        filters = []
        if self.is_owned:
            filters.append(self.entity.account == self.request.account)

        if not deleted:
            filters.append(self.entity.deleted==False)
        return self.entity.query.filter(*filters)

    def get_id(self):
        """
        Help support using both integer id's and uuid
        """
        query = self.filter()

        pk = self.entity.get_pk()
        if len(pk) != 1:
            raise RuntimeError("Couldn't get pk automatically")

        obj = query.filter_by(**{pk[0]: self.id_}).first()
        if not obj:
            raise exceptions.HTTPNotFound
        return obj

    def get(self):
        obj = self.get_id()
        return obj.serialize()

    def post(self):
        obj = self.get_id()
        obj.from_dict(self.request.json)
        return obj.serialize()

    def delete(self):
        obj = self.get_id()
        obj.delete()
        return {"status": "ok"}

    def collection_get(self):
        opts = search_options(self.request)
        query = self.filter()
        collection = self.entity.search(query=query, **opts)
        return self.render_collection(collection)

    def collection_post(self):
        obj = self.entity().from_dict(self.request.json)
        obj.account_id = self.request.account.id
        return obj.save().serialize()


def require_account(request):
    if not request.account:
        request.errors.add("account", "required",
                "Missing account in request or default not set")


@resource(path="/user/account", permission="view")
class UserAccountAPI(APIBase):
    entity = m.Account

    def get_id(self):
        return self.request.user.get_group(self.id_)

    def get(self):
        """
        This gives you a users accounts
        """
        user = self.request.user
        # NOTE: If current is not set and the user has only 1 account we switch
        # to it
        default = user.default_account.serialize() if user.default_account else None
        return {
                "accounts": self.render_collection(user.accounts),
                "default": default}

    def post(self):
        try:
            id_ = self.request.json["accountId"]
        except KeyError:
            raise exceptions.HTTPForbidden

        group = self.request.user.get_group(id_)
        if not group:
            raise exceptions.HTTPForbidden

        self.request.user.default_account_id = group.id
        self.request.user.save()
        return self.get()


@resource(collection_path="/{account}/category", path="/{account}/category/{id}",
        permission="view", validators=require_account)
class CategoryAPI(APIBase):
    entity = m.Category

    def get_id(self):
        obj = self.entity.query.filter_by(
                resource_id=self.id_,
                owner_group_id=self.request.account.id).first()
        return obj

    def collection_get(self):
        query = m.Category.query.filter(
                m.Resource.owner_group_id==self.request.account.id)
        collection = m.Category.search(query=query)
        return [row.serialize() for row in collection]

    def collection_post(self):
        return {}


@resource(collection_path="/{account}/booking", path="/{account}/booking/{id}",
        permission="view", validators=require_account)
class BookingAPI(APIBase):
    entity = m.Booking


@resource(collection_path="/{account}/customer", path="/{account}/customer/{id}",
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


@resource(collection_path="/user/message", path="/user/message/{id}", permission="view")
class MessagesAPI(APIBase):
    entity = m.Message


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
