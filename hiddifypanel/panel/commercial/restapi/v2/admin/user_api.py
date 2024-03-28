from flask import g
from flask.views import MethodView
from flask import current_app as app
from apiflask import abort
from hiddifypanel.auth import login_required
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from hiddifypanel.panel import hiddify

from . import has_permission
from .schema import UserSchema, PatchUserSchema, SuccessfulSchema


class UserApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(UserSchema)  # type: ignore
    def get(self, uuid):
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")

        return user.to_dict(False)  # type: ignore

    @app.input(PatchUserSchema, arg_name="data")  # type: ignore
    @app.output(SuccessfulSchema)  # type: ignore
    def patch(self, uuid, data):
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")

        data['uuid'] = uuid
        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        User.add_or_update(**data)  # type: ignore
        user = User.by_uuid(uuid) or abort(502, "unknown issue! user is not added")
        user_driver.add_client(user)
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}

    @app.output(SuccessfulSchema)  # type: ignore
    def delete(self, uuid):
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")
        user.remove()  # type: ignore
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}
