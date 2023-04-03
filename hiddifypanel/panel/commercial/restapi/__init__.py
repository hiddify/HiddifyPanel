from flask import Blueprint
from flask_restful import Api


from . import tgbot 
bp = Blueprint("api", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v1")
api = Api(bp)


def init_app(app):   
    api.add_resource(tgbot.TGBotResource, "/tgbot/")
    with app.app_context():
        tgbot.register_bot()        
    app.register_blueprint(bp)
