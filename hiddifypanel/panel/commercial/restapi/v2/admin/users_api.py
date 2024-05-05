from flask.views import MethodView
from flask import current_app as app, g
from apiflask import abort
from hiddifypanel.auth import login_required
from hiddifypanel.models.role import Role
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from hiddifypanel.models import User
from .user_api import UserSchema
from . import has_permission


class UsersApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(UserSchema(many=True))  # type: ignore
    def get(self):
        users = User.query.filter(User.added_by.in_(g.account.recursive_sub_admins_ids())).all() or abort(404, "You have no user")
        return [user.to_schema() for user in users]  # type: ignore
