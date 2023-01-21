from flask import Blueprint
from flask_restful import Api

from .resources import *

bp = Blueprint("restapi", __name__, url_prefix="/admin/api/v1")
api = Api(bp)


def init_app(app):
    api.add_resource(UserResource, "/users/")
    api.add_resource(DomainResource, "/domains/")
    api.add_resource(StrConfigResource, "/str_configs/")
    api.add_resource(BoolConfigResource, "/bool_configs/")
    api.add_resource(AllResource, "/all/")
    
    app.register_blueprint(bp)
