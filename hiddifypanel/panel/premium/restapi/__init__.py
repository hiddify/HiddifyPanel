from flask import Blueprint
from flask_restful import Api

from .resources import *
from .update_usage import UpdateUsageResource
from .parent_child import *
from .tgbot import TGBotResource
from . import tgbot 
bp = Blueprint("api", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v1")
api = Api(bp)


def init_app(app):
    api.add_resource(UserResource, "/users/","/users/<uuid:uuid>")
    api.add_resource(DomainResource, "/domains/","/domains/<string:domain>")
    api.add_resource(ParentDomainResource, "/parent_domains/","/parent_domains/<string:domain>")
    api.add_resource(ConfigResource, "/configs/","/configs/<string:key>/")
    
    api.add_resource(AllResource, "/all/")
    api.add_resource(UpdateUsageResource, "/update_usage/")
    api.add_resource(HelloResource, "/hello/")
    api.add_resource(SyncChildResource, "/sync_child/")
    api.add_resource(AddUsageResource, "/add_usage/")
    api.add_resource(TGBotResource, "/tgbot/")
    with app.app_context():
        tgbot.register_bot()        
    app.register_blueprint(bp)
