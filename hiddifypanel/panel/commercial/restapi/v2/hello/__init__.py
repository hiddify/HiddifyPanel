from flask_apispec import FlaskApiSpec
from flask_apispec.extension import FlaskApiSpec
from marshmallow import Schema, fields

from flask import Blueprint
from apiflask import APIBlueprint

bp = APIBlueprint("api_hello", __name__, url_prefix="/<proxy_path>/api/v2/hello/", enable_openapi=True)


def init_app(app):

    with app.app_context():
        from .hello import Hello
        bp.add_url_rule('/', view_func=Hello.as_view('hello'))
    app.register_blueprint(bp)
