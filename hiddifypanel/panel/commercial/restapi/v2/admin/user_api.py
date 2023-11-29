from flask import jsonify, request
# from flask_simplelogin import login_required
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from hiddifypanel.panel import hiddify

from flask.views import MethodView

from flask import current_app as app
from apiflask import abort,Schema
from apiflask.fields import UUID,String,Float,Enum,Date,Integer,DateTime


class UserSchema(Schema):
    uuid = UUID(required=True, description="Unique identifier for the user")
    name = String(required=True, description="Name of the user")

    usage_limit_GB = Float(
        required=False,
        allow_none=True,
        description="The data usage limit for the user in gigabytes"
    )
    package_days = Integer(
        required=False,
        allow_none=True,
        description="The number of days in the user's package"
    )
    mode = Enum(UserMode,
                required=False,
                allow_none=True,
                description="The mode of the user's account, which dictates access level or type"
                )
    last_online = DateTime(
        format="%Y-%m-%d %H:%M:%S",
        allow_none=True,
        description="The last time the user was online, converted to a JSON-friendly format"
    )
    start_date = Date(
        format='%Y-%m-%d',
        allow_none=True,
        description="The start date of the user's package, in a JSON-friendly format"
    )
    current_usage_GB = Float(
        required=False,
        allow_none=True,
        description="The current data usage of the user in gigabytes"
    )
    last_reset_time = Date(
        format='%Y-%m-%d',
        description="The last time the user's data usage was reset, in a JSON-friendly format",
        allow_none=True
    )
    comment = String(
        missing=None,
        allow_none=True,
        description="An optional comment about the user"
    )
    added_by_uuid = UUID(
        required=True,
        description="UUID of the admin who added this user",
        # validate=OneOf([p.uuid for p in AdminUser.query.all()])
    )
    telegram_id = Integer(
        required=False,
        allow_none=True,
        description="The Telegram ID associated with the user"
    )
    ed25519_private_key = String(
        required=False,
        allow_none=True,
        description="If empty, it will be created automatically, The user's private key using the Ed25519 algorithm"
    )
    ed25519_public_key = String(
        required=False,
        allow_none=True,
        description="If empty, it will be created automatically,The user's public key using the Ed25519 algorithm"
    )



class UserApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.output(UserSchema)
    def get(self, uuid):
        user = user_by_uuid(uuid) or abort(404, "user not found")
        return user.to_dict(False)

    @app.input(UserSchema, arg_name="data")
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
