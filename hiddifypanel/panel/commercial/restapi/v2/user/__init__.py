from flask_apispec import FlaskApiSpec
from flask_apispec.extension import FlaskApiSpec
from marshmallow import Schema, fields


from flask import Blueprint
from flask_restful import Api
from apiflask import APIBlueprint

bp = APIBlueprint("api_user", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v2/user/", enable_openapi=True)


def init_app(app):
    with app.app_context():
        from .user import InfoAPI,MTProxiesAPI,AllConfigsAPI,ShortAPI,AppAPI
        bp.add_url_rule("/me/", view_func=InfoAPI)
        bp.add_url_rule("/mtproxies/", view_func=MTProxiesAPI)
        bp.add_url_rule("/all-configs/", view_func=AllConfigsAPI)
        bp.add_url_rule("/short/", view_func=ShortAPI)
        bp.add_url_rule('/apps/',view_func=AppAPI)

    app.register_blueprint(bp)
