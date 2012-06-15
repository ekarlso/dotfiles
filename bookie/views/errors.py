from pyramid.response import Response
from pyramid.view import view_config
from sqlalchemy.orm.exc import NoResultFound



@view_config(context=NoResultFound, renderer="bookie:templates/err/404.pt")
def sqla_404(exc, request):
    request.response.status_int = 404
    return {"first_heading": "Queried resource not found"}
