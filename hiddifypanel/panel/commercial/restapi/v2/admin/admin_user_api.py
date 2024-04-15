from flask import current_app as app
from flask import g
from flask.views import MethodView
from apiflask import abort
from hiddifypanel.auth import login_required
from hiddifypanel.models import *

from . import has_permission
from .schema import AdminSchema, PutAdminSchema, PatchAdminSchema, SuccessfulSchema


class AdminUserApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin})]

    @app.output(AdminSchema)  # type: ignore
    def get(self, uuid):
        admin = AdminUser.by_uuid(uuid) or abort(404, "Admin not found")
        if not has_permission(admin):
            abort(403, "you don't have permission to access this admin")
        return admin.to_schema()  # type: ignore

    @app.input(PutAdminSchema, arg_name='data')  # type: ignore
    @app.output(SuccessfulSchema)  # type: ignore
    def put(self, uuid, data):
        if AdminUser.by_uuid(uuid):
            abort(400, "The admin exists")
        data['uuid'] = uuid

        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        _ = AdminUser.add_or_update(**data) or abort(502, "Unknown issue: Admin is not added")
        return {'status': 200, 'msg': 'ok'}

    @app.input(PatchAdminSchema, arg_name='data')  # type: ignore
    @app.output(SuccessfulSchema)  # type: ignore
    def patch(self, uuid, data):
        admin = AdminUser.by_uuid(uuid) or abort(404, "Admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")

        for field in AdminUser.__table__.columns.keys():  # type: ignore
            if field in ['id', 'parent_admin_id']:
                continue
            if field not in data:
                data[field] = getattr(admin, field)

        _ = AdminUser.add_or_update(True, **data) or abort(502, "Unknown issue: Admin is not patched")
        # the add_or_update doesn't update the uuid of AdminUser, so for now just delete old admin after adding new
        if admin.uuid != data['uuid']:
            admin.remove()
        return {'status': 200, 'msg': 'ok'}

    @app.output(SuccessfulSchema)  # type: ignore
    def delete(self, uuid):
        admin = AdminUser.by_uuid(uuid) or abort(404, "Admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        admin.remove()  # type: ignore
        return {'status': 200, 'msg': 'ok'}
