from flask import abort, jsonify, request
from flask_restful import Resource
# from flask_simplelogin import login_required
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify

from flask.views import MethodView

from flask import current_app as app
from flask import g
from apiflask import abort

from hiddifypanel.models import *
from hiddifypanel.panel.commercial.restapi.v2.admin.DTO import *


class AdminInfoApi(MethodView):
    decorators = [hiddify.super_admin]
    @app.output(AdminDTO)
    def get(self):
        # in this case g.user_uuid is equal to admin uuid
        admin_uuid = g.user_uuid
        admin = get_admin_user_db(admin_uuid) or abort(404, "user not found")

        dto = AdminDTO()
        dto.name = admin.name
        dto.comment = admin.comment
        dto.uuid = admin.uuid
        dto.mode = admin.mode
        dto.can_add_admin = admin.can_add_admin
        dto.parent_admin_uuid = AdminUser.query.filter(AdminUser.id == admin.parent_admin_id).first().uuid or 'None'
        dto.telegram_id = admin.telegram_id
        dto.lang =  Lang(hconfig(ConfigEnum.admin_lang))
        return dto
class AdminUsersApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(AdminDTO(many=True))
    def get(self):
        admins = AdminUser.query.all() or abort(502, "WTF!")
        return [admin.to_dict() for admin in admins]

    @app.input(AdminDTO, arg_name='data')
    @app.output(AdminDTO)
    def put(self, data):
        # data = request.json
        # uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        dbuser = hiddify.add_or_update_admin(**data)

        return dbuser.to_dict()


class AdminUserApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(AdminDTO)
    def get(self, uuid):

        admin = get_admin_user_db(uuid) or abort(404, "user not found")
        return admin.to_dict()

    @app.input(AdminDTO, arg_name='data')
    def patch(self, uuid, data):
        data['uuid'] = uuid
        hiddify.add_or_update_admin(**data)
        return {'status': 200, 'msg': 'ok'}

    def delete(self, uuid):
        admin = get_admin_user_db(uuid) or abort(404, "admin not found")
        admin.remove()
        return {'status': 200, 'msg': 'ok'}
    
class AdminServerStatus(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(ServerStatus)
    def get(self):
        dto = ServerStatus()
        dto.stats = {
            'system': hiddify.system_stats(),
            'top5': hiddify.top_processes()
        }
        admin_id = request.args.get("admin_id") or g.admin.id
        dto.usage_history = get_daily_usage_stats(admin_id)
        return dto