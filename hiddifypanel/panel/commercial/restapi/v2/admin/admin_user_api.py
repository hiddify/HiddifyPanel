
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
    decorators = [login_required({Role.admin})]

    @app.output(AdminSchema)
    def get(self, uuid):
        admin = get_admin_by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        return admin.to_dict()

    @app.input(AdminSchema, arg_name='data')
    def patch(self, uuid, data):
        admin = get_admin_by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        data['uuid'] = uuid
        hiddify.add_or_update_admin(**data)
        return {'status': 200, 'msg': 'ok'}

    def delete(self, uuid):
        admin = get_admin_by_uuid(uuid) or abort(404, "admin not found")
        if not has_permission(admin):
            abort(403, "You don't have permission to access this admin")
        admin.remove()
        return {'status': 200, 'msg': 'ok'}


def has_permission(admin) -> bool:
    '''Check if the authenticated account has permission to do an action(get,insert,update,delete) on the admin another admin'''
    if not g.account.uuid != get_super_admin_uuid() and admin.parent_admin_id != g.account.id:  # type: ignore
        return False
    return True
