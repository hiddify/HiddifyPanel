from flask import abort, jsonify, request
# from flask_simplelogin import login_required
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from hiddifypanel.panel import hiddify

from flask.views import MethodView

from flask import current_app as app
from apiflask import abort

from hiddifypanel.panel.commercial.restapi.v2.admin.DTO import *

class UsersApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(UserDTO(many=True))
    def get(self):
        users = User.query.all() or abort(502, "WTF!")
        return [user.to_dict(False) for user in users]

    @app.input(UserDTO, arg_name="data")
    @app.output(UserDTO)
    def put(self, data):
        hiddify.add_or_update_user(**data)
        user = user_by_uuid(data['uuid']) or abort(502, "unknown issue! user is not added")
        user_driver.add_client(user)
        hiddify.quick_apply_users()
        return user.to_dict(False)


class UserApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(UserDTO)
    def get(self, uuid):
        user = user_by_uuid(uuid) or abort(404, "user not found")
        return user.to_dict(False)

    @app.input(UserDTO, arg_name="data")
    def patch(self, uuid, data):
        data = request.json
        uuid = data.get('uuid') or abort(422, "Parameter issue: 'uuid'")
        hiddify.add_or_update_user(**data)
        user = user_by_uuid(uuid) or abort(502, "unknown issue! user is not added")
        user_driver.add_client(user)
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}

    def delete(self, uuid):
        user = user_by_uuid(uuid) or abort(404, "user not found")
        user.remove()
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}
