from flask import Blueprint
from flask_restful import Api

from .resources import *
from .update_usage import UpdateUsageResource
from .parent_child import *
bp = Blueprint("api", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v1")
api = Api(bp)


def init_app(app):
    api.add_resource(UserResource, "/users/")
    api.add_resource(DomainResource, "/domains/")
    api.add_resource(StrConfigResource, "/str_configs/")
    api.add_resource(BoolConfigResource, "/bool_configs/")
    api.add_resource(AllResource, "/all/")
    api.add_resource(UpdateUsageResource, "/update_usage/")
    api.add_resource(HelloResource, "/hello/")
    api.add_resource(SyncChildResource, "/sync_child/")
    api.add_resource(AddUsageResource, "/add_usage/")
    
    app.register_blueprint(bp)
