from flask_apispec import FlaskApiSpec
from flask_apispec.extension import FlaskApiSpec
from marshmallow import Schema, fields


from flask import Blueprint
from flask_restful import Api
from apiflask import APIBlueprint

bp = APIBlueprint("api_user", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v2/user/", enable_openapi=True)


def init_app(app):
    with app.app_context():
        from .info import Info
        bp.add_url_rule("info", view_func=Info)
    app.register_blueprint(bp)
