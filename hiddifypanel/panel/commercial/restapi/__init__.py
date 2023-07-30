from flask import Blueprint
from flask_restful import Api
from .tgbot import bot, register_bot, TGBotResource
from . import tgbot
from .tgmsg import SendMsgResource
from .resources import *
bp = Blueprint("api", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v1")
api = Api(bp)


def init_app(app):
    tgbot.init_app(app)
    api.add_resource(TGBotResource, "/tgbot/")
    api.add_resource(SendMsgResource, "/send_msg/")
    api.add_resource(UserResource, "/user/")
    api.add_resource(AdminUserResource, "/admin/")

    # with app.app_context():
    #     register_bot()
    app.register_blueprint(bp)
