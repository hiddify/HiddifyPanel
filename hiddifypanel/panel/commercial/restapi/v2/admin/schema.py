import uuid
from apiflask.fields import String, Float, Enum, Date, Integer, Boolean, DateTime
from apiflask import Schema, fields
from typing import Any, Mapping

from marshmallow import ValidationError

from hiddifypanel.models import UserMode, Lang, AdminMode
from hiddifypanel import hutils

# region user api


class FriendlyDateTime(fields.Field):
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs):
        return hutils.convert.time_to_json(value)

    def _deserialize(self, value: Any, attr: str | None, data: Mapping[str, Any] | None, **kwargs):
        return hutils.convert.json_to_time(value)


class FriendlyUUID(fields.Field):

    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs):
        if value is None or not hutils.auth.is_uuid_valid(value):
            return None
        return str(value)

    def _deserialize(self, value: Any, attr: str | None, data: Mapping[str, Any] | None, **kwargs):
        if value is None or not hutils.auth.is_uuid_valid(value):
            return None
        try:
            return str(uuid.UUID(value))
        except ValueError:
            self.fail('Invalid uuid')

    def _validated(self, value):
        if not hutils.auth.is_uuid_valid(value):
            raise ValidationError('Invalid UUID')


class UserSchema(Schema):
    uuid = FriendlyUUID(required=True, description="Unique identifier for the user")
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
    last_reset_time = FriendlyDateTime(
        format='%Y-%m-%d %H:%M:%S',
        description="The last time the user's data usage was reset, in a JSON-friendly format",
        allow_none=True
    )
    # expiry_time = Date(
    #     format='%Y-%m-%d',
    #     description="The expiry time of the user's package, in a JSON-friendly format",
    #     allow_none=True
    # )
    comment = String(
        missing=None,
        allow_none=True,
        description="An optional comment about the user"
    )
    added_by_uuid = FriendlyUUID(
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
    enable = Boolean(required=False, description="Whether the user is enabled or not")
    is_active = Boolean(required=False, description="Whether the user is active for using hiddify")
    id = Integer(required=False, description="never use it, only for better presentation")


class PostUserSchema(UserSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # the uuid is sent in the url path
        self.fields['uuid'].required = False
        self.fields['uuid'].allow_none = True
        del self.fields['id']


class PatchUserSchema(UserSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['uuid'].required = False
        self.fields['uuid'].allow_none = True,
        self.fields['name'].required = False
        self.fields['name'].allow_none = True,
        del self.fields['id']


# endregion

# region admin api


class AdminSchema(Schema):
    name = String(required=True, description='The name of the admin')
    comment = String(required=False, description='A comment related to the admin', allow_none=True)
    uuid = FriendlyUUID(required=False, allow_none=True, description='The unique identifier for the admin')
    mode = Enum(AdminMode, required=True, description='The mode for the admin')
    can_add_admin = Boolean(required=True, description='Whether the admin can add other admins')
    parent_admin_uuid = FriendlyUUID(required=False, description='The unique identifier for the parent admin', allow_none=True,
                                     # validate=OneOf([p.uuid for p in AdminUser.query.all()])
                                     )
    telegram_id = Integer(required=False, description='The Telegram ID associated with the admin', allow_none=True)
    lang = Enum(Lang, required=True)
    max_users = Integer(required=False, description='The maximum number of users allowed', allow_none=True)
    max_active_users = Integer(required=False, description='The maximum number of active users allowed', allow_none=True)


class PatchAdminSchema(AdminSchema):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['uuid'].required = False
        self.fields['name'].required = False
        self.fields['mode'].required = False
        self.fields['lang'].required = False
        self.fields['can_add_admin'].required = False

# endregion


class SuccessfulSchema(Schema):
    status = Integer()
    msg = String()
