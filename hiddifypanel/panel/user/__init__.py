from flask import Blueprint
from hiddifypanel.panel.database import db

# from .resources import ProductItemResource, ProductResource
from .user import *
bp = Blueprint("user2", __name__, url_prefix="/<proxy_path>/<user_secret>/",template_folder="templates")


from flask import send_from_directory
from .user import UserView

def send_static(path):
    return send_from_directory('static/assets', path)

def init_app(app):
    UserView.register(bp,route_base="/")
    # bp.add_url_rule("/", view_func=index)
    # bp.add_url_rule("/<lang>", view_func=index)
    # bp.add_url_rule("/clash/<meta_or_normal>/<mode>.yml", view_func=clash_config)
    # bp.add_url_rule("/clash/<mode>.yml", view_func=clash_config)
    # bp.add_url_rule("/clash/<meta_or_normal>/proxies.yml", view_func=clash_proxies)
    # bp.add_url_rule("/clash/proxies.yml", view_func=clash_proxies)
    # bp.add_url_rule("/all.txt", view_func=all_configs)
    # bp.add_url_rule('/static/<path:path>',view_func=send_static)
    app.register_blueprint(bp)