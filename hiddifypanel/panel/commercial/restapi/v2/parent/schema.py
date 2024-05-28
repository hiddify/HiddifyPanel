from apiflask import fields, Schema
from marshmallow import ValidationError

from hiddifypanel.models import DomainType, ProxyProto, ProxyL3, ProxyTransport, ProxyCDN, ConfigEnum, ChildMode
from hiddifypanel.panel.commercial.restapi.v2.admin.schema import UserSchema, AdminSchema


def hconfig_key_validator(value):
    if value not in [c.name for c in ConfigEnum]:
        raise ValidationError(f"{value} is not a valid hconfig key.")
    return value


class DomainSchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    domain = fields.String(required=True, description="The domain name")
    alias = fields.String(description="The domain alias", allow_none=True)
    sub_link_only = fields.Boolean(required=True, description="Is the domain sub link only")
    mode = fields.Enum(DomainType, required=True, description="The domain type")
    cdn_ip = fields.String(description="The cdn ip", allow_none=True)
    grpc = fields.Boolean(required=True, description="Is the domain grpc")
    servernames = fields.String(description="The servernames", allow_none=True)
    show_domains = fields.List(fields.String(), desciption="The list of domains to show")


class ProxySchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    name = fields.String(required=True, description="The proxy name")
    enable = fields.Boolean(required=True, description="Is the proxy enabled")
    proto = fields.Enum(ProxyProto, required=True, description="The proxy protocol")
    l3 = fields.Enum(ProxyL3, required=True, description="The proxy l3")
    transport = fields.Enum(ProxyTransport, required=True, description="The proxy transport")
    cdn = fields.Enum(ProxyCDN, required=True, description="The proxy cdn")


class StringOrBooleanField(fields.Field):
    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, (str, bool)):
            return str(value)
        else:
            raise ValidationError("Value must be a string or a boolean.")

    def _serialize(self, value, attr, obj, **kwargs):
        return value


class HConfigSchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    key = fields.String(required=True, description="The config key", validate=hconfig_key_validator)  # type: ignore
    value = StringOrBooleanField(required=True, description="The config value")


# region usage
class UsageData(Schema):
    uuid = fields.UUID(required=True, desciption="The user uuid")
    usage = fields.Integer(required=True, description="The user usage in bytes")
    devices = fields.List(fields.String(required=True, description="The user connected devices"))


class UsageInputOutputSchema(Schema):
    usages = fields.List(fields.Nested(UsageData), required=True, description="The list of usages")
# endregion


# region sync
class SyncInputSchema(Schema):
    domains = fields.List(fields.Nested(DomainSchema), required=False, description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema), required=False, description="The list of proxies")
    hconfigs = fields.List(fields.Nested(HConfigSchema), required=False, description="The list of configs")
    # users = fields.List(fields.Nested(UserSchema),required=True,description="The list of users")
    # admin_users = fields.List(fields.Nested(AdminSchema),required=True,description="The list of admin users")

    def validate(self, data, **kwargs):
        if not (data.get("domains") or data.get("proxies") or data.get("hconfigs")):
            raise ValidationError("At least one field must exist (domains, proxies, or hconfigs)")
        return data


class SyncOutputSchema(Schema):
    users = fields.List(fields.Nested(UserSchema), required=True, description="The list of users")
    admin_users = fields.List(fields.Nested(AdminSchema), required=True, description="The list of admin users")

# endregion


# region child status
class ChildStatusInputSchema(Schema):
    child_unique_id = fields.String(required=True, description="The child's unique id")


class ChildStatusOutputSchema(Schema):
    existance = fields.Boolean(required=True, description="Whether child exists")

# end region


# region register

class RegisterDataSchema(Schema):
    users = fields.List(fields.Nested(UserSchema), required=True, description="The list of users")
    domains = fields.List(fields.Nested(DomainSchema), required=True, description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema), required=True, description="The list of proxies")
    admin_users = fields.List(fields.Nested(AdminSchema), required=True, description="The list of admin users")
    hconfigs = fields.List(fields.Nested(HConfigSchema), required=True, description="The list of configs")


class RegisterInputSchema(Schema):
    panel_data = fields.Nested(RegisterDataSchema, required=True, description="The child's data")
    unique_id = fields.String(required=True, description="The child's unique id")
    name = fields.String(required=True, description="The child's name")
    mode = fields.Enum(ChildMode, required=True, description="The child's mode")


class RegisterOutputSchema(Schema):
    parent_unique_id = fields.String(description="The parent's unique id")
    users = fields.List(fields.Nested(UserSchema), required=True, description="The list of users")
    admin_users = fields.List(fields.Nested(AdminSchema), required=True, description="The list of admin users")

# endregion
