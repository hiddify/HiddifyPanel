from flask import current_app as app
from flask import g
from flask.views import MethodView
from apiflask import abort
from hiddifypanel.panel.auth import login_required
from hiddifypanel.models.admin import AdminUser, get_admin_by_uuid
from hiddifypanel.models.config_enum import ConfigEnum, Lang
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.role import Role
from .admin_user_api import AdminSchema


class AdminInfoApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(AdminSchema)
    def get(self):
        # admin = get_admin_by_uuid(g.account.uuid) or abort(404, "user not found")
        admin = g.account or abort(404, "user not found")

        dto = AdminSchema()
        dto.name = admin.name
        dto.comment = admin.comment
        dto.uuid = admin.uuid
        dto.mode = admin.mode
        dto.can_add_admin = admin.can_add_admin
        dto.parent_admin_uuid = AdminUser.query.filter(AdminUser.id == admin.parent_admin_id).first().uuid or 'None'
        dto.telegram_id = admin.telegram_id or 0
        dto.lang = Lang(hconfig(ConfigEnum.admin_lang))
        return dto
