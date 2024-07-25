from flask_apispec import FlaskApiSpec
from flask_apispec.extension import FlaskApiSpec
from marshmallow import Schema, fields


from apiflask import APIBlueprint
from flask_restful import Api
from .tgbot import bot, register_bot, register_bot_cached, TGBotResource
from . import tgbot
from .tgmsg import SendMsgResource
from .resources import *
bp = APIBlueprint("api_v1", __name__, url_prefix="/<proxy_path>/api/v1/", tag="api_v1", enable_openapi=False)
bp_uuid = APIBlueprint("api_v1_uuid", __name__, url_prefix="/<proxy_path>/<uuid:secret_uuid>/api/v1/", template_folder="templates", enable_openapi=False)
api = Api(bp)
api_uuid = Api(bp_uuid)


def init_app(app):
    tgbot.init_app(app)
    api.add_resource(UserResource, "/user/")
    api.add_resource(AdminUserResource, "/admin/")
    # api.add_resource(TGBotResource, "/tgbot/")
    api.add_resource(SendMsgResource, "/send_msg/")

    api_uuid.add_resource(UserResource, "/user/")
    api_uuid.add_resource(AdminUserResource, "/admin/")
    api_uuid.add_resource(TGBotResource, "/tgbot/")
    api_uuid.add_resource(SendMsgResource, "/send_msg/")

    # with app.app_context():
    #     register_bot()
    app.register_blueprint(bp)
    app.register_blueprint(bp_uuid)
