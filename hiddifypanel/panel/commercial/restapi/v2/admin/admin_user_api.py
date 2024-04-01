from flask import current_app as app
from flask import g
from flask.views import MethodView
from apiflask import abort
from hiddifypanel.auth import login_required
from hiddifypanel.models import *

from . import has_permission
from .schema import AdminSchema, PatchAdminSchema, SuccessfulSchema


class AdminUserApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin})]

    @app.output(AdminSchema)  # type: ignore
    def get(self, uuid):
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        return admin.to_dict()  # type: ignore

    @app.input(PatchAdminSchema, arg_name='data')  # type: ignore
    @app.output(SuccessfulSchema)  # type: ignore
    def patch(self, uuid, data):
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")

        data['uuid'] = uuid
        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        AdminUser.add_or_update(**data)
        return {'status': 200, 'msg': 'ok'}

    @app.output(SuccessfulSchema)  # type: ignore
    def delete(self, uuid):
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        admin.remove()  # type: ignore
        return {'status': 200, 'msg': 'ok'}
