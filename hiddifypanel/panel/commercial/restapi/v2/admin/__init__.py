from flask_apispec import FlaskApiSpec
from flask_apispec.extension import FlaskApiSpec
from marshmallow import Schema, fields

from flask import Blueprint
from apiflask import APIBlueprint

bp = APIBlueprint("api_admin", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v2/admin/", enable_openapi=True)


def init_app(app):

    with app.app_context():
        from .admin_user import AdminUsersApi, AdminUserApi,AdminInfoApi
        bp.add_url_rule('/me/',view_func=AdminInfoApi)
        bp.add_url_rule('/admin_user/', view_func=AdminUsersApi)
        bp.add_url_rule('/admin_user/<uuid:uuid>', view_func=AdminUserApi)

        from .user import UserApi, UsersApi
        bp.add_url_rule('/user/', view_func=UsersApi)
        bp.add_url_rule('/user/<uuid:uuid>', view_func=UserApi)
    app.register_blueprint(bp)
