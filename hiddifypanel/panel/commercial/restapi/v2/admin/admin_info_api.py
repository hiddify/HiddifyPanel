from flask import current_app as app
from flask import g
from flask.views import MethodView
from apiflask import abort

from hiddifypanel.models.admin import AdminUser, get_admin_user_db
from hiddifypanel.models.config import hconfig
from hiddifypanel.models.config_enum import ConfigEnum, Lang
from hiddifypanel.panel import hiddify
from .admin_user_api import AdminSchema

class AdminInfoApi(MethodView):
    decorators = [hiddify.super_admin]
    @app.output(AdminSchema)
    def get(self):
        # in this case g.user_uuid is equal to admin uuid
        admin_uuid = g.user_uuid
        admin = get_admin_user_db(admin_uuid) or abort(404, "user not found")

        dto = AdminSchema()
        dto.name = admin.name
        dto.comment = admin.comment
        dto.uuid = admin.uuid
        dto.mode = admin.mode
        dto.can_add_admin = admin.can_add_admin
        dto.parent_admin_uuid = AdminUser.query.filter(AdminUser.id == admin.parent_admin_id).first().uuid or 'None'
        dto.telegram_id = admin.telegram_id
        dto.lang =  Lang(hconfig(ConfigEnum.admin_lang))
        return dto