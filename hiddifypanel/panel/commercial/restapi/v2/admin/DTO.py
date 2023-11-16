from apiflask import Schema
from apiflask.fields import Integer, String, UUID, Boolean, Enum, Float, Date, Time
from hiddifypanel.models import AdminMode,UserMode,Lang

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
    lang = Enum(Lang,required=True)




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
        # validate=OneOf([p.uuid for p in AdminUser.query.all()])
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

