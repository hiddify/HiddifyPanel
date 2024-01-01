
from apiflask.fields import Integer, String, UUID, Boolean, Enum
from flask import current_app as app
from flask import g
from flask.views import MethodView
from apiflask import Schema
from apiflask import abort
from hiddifypanel.panel.auth import login_required
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.models import AdminMode, Lang

from . import SuccessfulSchema, has_permission


class AdminSchema(Schema):
    name = String(required=True, description='The name of the admin')
    comment = String(required=False, description='A comment related to the admin', allow_none=True)
    uuid = UUID(required=True, description='The unique identifier for the admin')
    mode = Enum(AdminMode, required=True, description='The mode for the admin')
    can_add_admin = Boolean(required=True, description='Whether the admin can add other admins')
    parent_admin_uuid = UUID(description='The unique identifier for the parent admin', allow_none=True,
                             # validate=OneOf([p.uuid for p in AdminUser.query.all()])
                             )
    telegram_id = Integer(required=False, description='The Telegram ID associated with the admin', allow_none=True)
    lang = Enum(Lang, required=True)


class AdminUserApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin})]

    @app.output(AdminSchema)
    def get(self, uuid):
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        return admin.to_dict()

    @app.input(AdminSchema, arg_name='data')
    @app.output(SuccessfulSchema)
    def patch(self, uuid, data):
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")

        data['uuid'] = uuid
        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        AdminUser.add_or_update(**data)
        return {'status': 200, 'msg': 'ok'}

    @app.output(SuccessfulSchema)
    def delete(self, uuid):
        admin = AdminUser.by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        admin.remove()
        return {'status': 200, 'msg': 'ok'}
