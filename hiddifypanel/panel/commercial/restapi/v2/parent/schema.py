from apiflask import fields, Schema
from marshmallow import ValidationError

from hiddifypanel.models import DomainType, ProxyProto, ProxyL3, ProxyTransport, ProxyCDN, ConfigEnum
from hiddifypanel.panel.commercial.restapi.v2.admin.user_api import UserSchema
from hiddifypanel.panel.commercial.restapi.v2.admin.admin_user_api import AdminSchema


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


class HConfigSchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    key = fields.String(required=True, description="The config key", validate=hconfig_key_validator)  # type: ignore
    value = fields.String(required=True, description="The config value")
