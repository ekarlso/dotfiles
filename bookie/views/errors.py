from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound



@view_config(context=NoResultFound, renderer="err/404.mako")
def sqla_404(exc, request):
    request.response.status_int = 404
    return {"sub_title": "Queried resource not found"}
