from flask import abort, jsonify, request
from flask_restful import Resource
# from flask_simplelogin import login_required
import datetime
from hiddifypanel.models import *
from urllib.parse import urlparse
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from flask_restful import Resource
from hiddifypanel.panel import hiddify

from flask_classful import FlaskView, route
from flask.views import MethodView

from flask import current_app as app
from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String
from apiflask.validators import Length, OneOf

from apiflask import APIFlask, Schema, abort
from apiflask.fields import Integer, String, UUID, Boolean, Enum, Float, Date, Time
from apiflask.validators import Length, OneOf

from hiddifypanel.models import *


class UserDTO(Schema):
    uuid = UUID(required=True, description="Unique identifier for the user")
    name = String(required=True, description="Name of the user")

    usage_limit_GB = Float(
        required=False,
        description="The data usage limit for the user in gigabytes"
    )
    package_days = Integer(
        required=False,
        description="The number of days in the user's package"
    )
    mode = Enum(UserMode,
                required=False,
                description="The mode of the user's account, which dictates access level or type"
                )
    last_online = Time(
        format="%Y-%m-%d %H:%M:%S",
        description="The last time the user was online, converted to a JSON-friendly format"
    )
    start_date = Date(
        format='%Y-%m-%d',
        description="The start date of the user's package, in a JSON-friendly format"
    )
    current_usage_GB = Float(
        required=False,
        description="The current data usage of the user in gigabytes"
    )
    last_reset_time = Date(
        format='%Y-%m-%d',
        description="The last time the user's data usage was reset, in a JSON-friendly format"
    )
    comment = String(
        missing=None,
        description="An optional comment about the user"
    )
    added_by_uuid = UUID(
        required=True,
        description="UUID of the admin who added this user",
        validate=OneOf([p.uuid for p in AdminUser.query.all()])
    )
    telegram_id = Integer(
        required=False,
        description="The Telegram ID associated with the user"
    )
    ed25519_private_key = String(
        required=False,
        description="If empty, it will be created automatically, The user's private key using the Ed25519 algorithm"
    )
    ed25519_public_key = String(
        required=False,
        description="If empty, it will be created automatically,The user's public key using the Ed25519 algorithm"
    )


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
        user = user_by_uuid(uuid) or abort(502, "unknown issue! user is not added")
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
