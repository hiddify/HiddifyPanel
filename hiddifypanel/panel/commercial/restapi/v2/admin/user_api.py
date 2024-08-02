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
from .schema import UserSchema, PostUserSchema, PatchUserSchema, SuccessfulSchema


class UserApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(UserSchema)  # type: ignore
    def get(self, uuid):
        """User: Get details of a user"""
        user = User.by_uuid(uuid) or abort(404, "User not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")

        return user.to_schema()  # type: ignore

    @app.input(PatchUserSchema, arg_name="data")  # type: ignore
    @app.output(UserSchema)  # type: ignore
    def patch(self, uuid, data):
        """User: Update a user"""
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")

        for field in User.__table__.columns.keys():  # type: ignore
            if field in ['id', 'expiry_time']:
                continue
            # if field in data:
            #     setattr(user, field, data[field])
        data['old_uuid'] = uuid
        user_driver.remove_client(user)
        dbuser = User.add_or_update(**data) or abort(502, "Unknown issue! User is not patched")
        if dbuser.is_active:
            user_driver.add_client(dbuser)
        # the add_or_update doesn't update the uuid of User, so for now just delete old user after adding new
        # if user.uuid != data['uuid']:
        #     user.remove()
        hiddify.quick_apply_users()
        return dbuser.to_schema()

    @app.output(SuccessfulSchema)  # type: ignore
    def delete(self, uuid):
        """User: Delete a User"""
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")
        user.remove()  # type: ignore
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}
