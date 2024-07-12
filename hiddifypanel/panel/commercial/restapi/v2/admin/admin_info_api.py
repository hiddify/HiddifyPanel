from flask import current_app as app
from flask import g
from flask.views import MethodView
from apiflask import abort
from hiddifypanel.auth import login_required
from hiddifypanel.models.admin import AdminMode, AdminUser
from hiddifypanel.models.config_enum import ConfigEnum, Lang
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.role import Role
from .schema import AdminSchema


class AdminInfoApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(AdminSchema)  # type: ignore
    def get(self):
        """Current Admin Info"""
        admin = g.account or abort(404, "user not found")

        dto = AdminSchema()
        dto.name = admin.name  # type: ignore
        dto.comment = admin.comment  # type: ignore
        dto.uuid = admin.uuid  # type: ignore
        dto.mode = admin.mode  # type: ignore
        dto.can_add_admin = admin.can_add_admin  # type: ignore
        if g.account.mode == AdminMode.super_admin:
            if parent := AdminUser.by_id(admin.parent_admin_id):
                dto.parent_admin_uuid = parent.uuid
        dto.telegram_id = admin.telegram_id or 0  # type: ignore
        dto.lang = Lang(hconfig(ConfigEnum.admin_lang))  # type: ignore
        return dto
