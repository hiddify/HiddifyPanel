from typing import Any, Mapping
from flask import g
from flask.views import MethodView
from flask import current_app as app
from apiflask import abort, Schema, fields
from hiddifypanel.auth import login_required
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from hiddifypanel.drivers import user_driver
from hiddifypanel.panel import hiddify
from apiflask.fields import UUID, String, Float, Enum, Date, Time, Integer, DateTime

from hiddifypanel import hutils
from . import SuccessfulSchema, has_permission


class FriendlyDateTime(fields.Field):
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs):
        return hutils.convert.time_to_json(value)

    def _deserialize(self, value: Any, attr: str | None, data: Mapping[str, Any] | None, **kwargs):
        return hutils.convert.json_to_time(value)


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
    last_online = FriendlyDateTime(
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
        required=False,
        description="UUID of the admin who added this user",
        allow_none=True,
        # validate=OneOf([p.uuid for p in AdminUser.query.all()])
    )
    telegram_id = Integer(
        required=False,
        description="The Telegram ID associated with the user",
        allow_none=True
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
    wg_pk = String(
        required=False,
        allow_none=True,
        description="If empty, it will be created automatically, The user's WireGuard private key"
    )

    wg_pub = String(
        required=False,
        allow_none=True,
        description="If empty, it will be created automatically, The user's WireGuard public key"
    )
    wg_psk = String(
        required=False,
        allow_none=True,
        description="If empty, it will be created automatically, The user's WireGuard preshared key"
    )

    lang = Enum(Lang, required=False, allow_none=True, description="The language of the user")


class PatchUserSchema(UserSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = False
    pass


class UserApi(MethodView):
    decorators = [login_required({Role.super_admin, Role.admin, Role.agent})]

    @app.output(UserSchema)
    def get(self, uuid):
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")

        return user.to_dict(False)

    @app.input(PatchUserSchema, arg_name="data")
    @app.output(SuccessfulSchema)
    def patch(self, uuid, data):
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")

        data['uuid'] = uuid
        if not data.get('added_by_uuid'):
            data['added_by_uuid'] = g.account.uuid

        User.add_or_update(**data)  # type: ignore
        user = User.by_uuid(uuid) or abort(502, "unknown issue! user is not added")
        user_driver.add_client(user)
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}

    @app.output(SuccessfulSchema)
    def delete(self, uuid):
        user = User.by_uuid(uuid) or abort(404, "user not found")
        if not has_permission(user):
            abort(403, "You don't have permission to access this user")
        user.remove()
        hiddify.quick_apply_users()
        return {'status': 200, 'msg': 'ok'}
