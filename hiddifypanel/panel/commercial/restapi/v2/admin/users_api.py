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
        return [user.to_dict(False) for user in users]  # type: ignore

    @app.input(UserSchema, arg_name="data")  # type: ignore
    @app.output(UserSchema)  # type: ignore
    def put(self, data):
        uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        user = User.by_uuid(uuid)  # type: ignore

        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        # update check permission
        if user:
            if not has_permission(user):
                abort(403, "You don't have permission to access this user")
        User.add_or_update(**data)  # type: ignore

        dbuser = User.by_uuid(data['uuid']) or abort(502, "Unknown issue: User is not added")
        user_driver.add_client(dbuser)
        hiddify.quick_apply_users()
        return dbuser.to_dict(False)  # type: ignore
