from flask import abort, jsonify, request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver

from flask.views import MethodView

from flask import current_app as app
from apiflask import APIFlask, Schema, abort
from apiflask.validators import Length, OneOf
from apiflask.fields import Integer, String, UUID, Boolean, Enum, Float, Date, Time

from hiddifypanel.models import *


class AdminDTO(Schema):
    name = String(required=True, description='The name of the admin')
    comment = String(required=False, description='A comment related to the admin')
    uuid = UUID(required=True, description='The unique identifier for the admin')
    mode = Enum(AdminMode, required=True, description='The mode for the admin')
    can_add_admin = Boolean(required=True, description='Whether the admin can add other admins')
    parent_admin_uuid = UUID(description='The unique identifier for the parent admin', allow_none=True,
                             # validate=OneOf([p.uuid for p in AdminUser.query.all()])
                             )
    telegram_id = Integer(required=True, description='The Telegram ID associated with the admin')


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
