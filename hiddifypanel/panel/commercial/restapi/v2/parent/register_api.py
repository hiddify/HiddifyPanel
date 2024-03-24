from apiflask import abort, Schema, fields
from hiddifypanel.database import db
from flask import current_app as app
from flask.views import MethodView

from hiddifypanel.models import *
from hiddifypanel.panel.commercial.restapi.v2.admin.user_api import UserSchema
from hiddifypanel.panel.commercial.restapi.v2.admin.admin_user_api import AdminSchema
from hiddifypanel.auth import login_required
from hiddifypanel.panel.commercial.restapi.v2.parent import hconfig_key_validator


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


class RegisterDataSchema(Schema):
    users = fields.List(fields.Nested(UserSchema), required=True, description="The list of users")
    domains = fields.List(fields.Nested(DomainSchema), required=True, description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema), required=True, description="The list of proxies")
    admin_users = fields.List(fields.Nested(AdminSchema), required=True, description="The list of admin users")
    hconfigs = fields.List(fields.Nested(HConfigSchema), required=True, description="The list of configs")


class RegisterSchema(Schema):
    panel_data = fields.Nested(RegisterDataSchema, required=True, description="The child's data")
    unique_id = fields.String(required=True, description="The child's unique id")
    name = fields.String(required=True, description="The child's name")
    mode = fields.Enum(ChildMode, required=True, description="The child's mode")


class OutputUsersSchema(Schema):
    users = fields.List(fields.Nested(UserSchema), required=True, description="The list of users")
    admin_users = fields.List(fields.Nested(AdminSchema), required=True, description="The list of admin users")


class RegisterApi(MethodView):
    decorators = [login_required(child_parent_auth=True)]

    @app.input(RegisterSchema, arg_name='data')  # type: ignore
    @app.output(OutputUsersSchema)  # type: ignore
    def put(self, data):
        unique_id = data['unique_id']
        name = data['name']
        mode = data['mode']

        child = Child.query.filter(Child.unique_id == unique_id).first()
        if not child:
            child = Child(unique_id=unique_id, name=name, mode=mode)
            db.session.add(child)  # type: ignore
            db.session.commit()  # type: ignore
            child = Child.query.filter(Child.unique_id == unique_id).first()

        try:
            # add data
            AdminUser.bulk_register(data['panel_data']['admin_users'], commit=False)
            User.bulk_register(data['panel_data']['users'], commit=False)
            bulk_register_domains(data['panel_data']['domains'], commit=False, force_child_unique_id=child.unique_id)
            bulk_register_configs(data['panel_data']['hconfigs'], commit=False, froce_child_unique_id=child.unique_id)
            Proxy.bulk_register(data['panel_data']['proxies'], commit=False, force_child_unique_id=child.unique_id)
            db.session.commit()  # type: ignore
        except Exception as err:
            abort(400, str(err))

        if hconfig(ConfigEnum.panel_mode) != PanelMode.parent:
            set_hconfig(ConfigEnum.panel_mode, PanelMode.parent)
        return self.__create_response()

    def __create_response(self) -> OutputUsersSchema:
        '''Create response for parent register api'''
        res = OutputUsersSchema()
        res.users = [u.to_schema() for u in User.query.all()]  # type: ignore
        res.admin_users = [a.to_schema() for a in AdminUser.query.all()]  # type: ignore

        return res
