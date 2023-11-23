from flask_apispec import FlaskApiSpec
from flask_apispec.extension import FlaskApiSpec
from marshmallow import Schema, fields

from flask import Blueprint
from apiflask import APIBlueprint

bp = APIBlueprint("api_admin", __name__, url_prefix="/<proxy_path>/<user_secret>/api/v2/admin/", enable_openapi=True)


def init_app(app):

    with app.app_context():
        from .admin_info_api import AdminInfoApi
        from .server_status_api import AdminServerStatusApi
        from .admin_user_api import AdminUserApi
        from .admin_users_api import AdminUsersApi
        bp.add_url_rule('/me/',view_func=AdminInfoApi)
        bp.add_url_rule('/server_status/',view_func=AdminServerStatusApi)
        bp.add_url_rule('/admin_user/<uuid:uuid>', view_func=AdminUserApi)
        bp.add_url_rule('/admin_user/', view_func=AdminUsersApi)

        from .user_api import UserApi
        from .users_api import UsersApi
        bp.add_url_rule('/user/<uuid:uuid>', view_func=UserApi)
        bp.add_url_rule('/user/', view_func=UsersApi)
    app.register_blueprint(bp)
