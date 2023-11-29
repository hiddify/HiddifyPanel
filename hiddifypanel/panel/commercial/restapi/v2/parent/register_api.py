from apiflask import fields
from apiflask import abort,Schema
from hiddifypanel.models import DomainType,ProxyProto,ProxyTransport,ProxyCDN,ProxyL3,ConfigEnum,Child,User
from hiddifypanel.models.admin import AdminUser
from hiddifypanel.panel.database import db
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.commercial.restapi.v2.admin.user_api import UserSchema
from hiddifypanel.panel.commercial.restapi.v2.admin.admin_user_api import AdminSchema
from flask import current_app as app
from flask.views import MethodView


class DomainSchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    domain = fields.String(required=True,description="The domain name")
    alias = fields.String(description="The domain alias",allow_none=True)
    sub_link_only = fields.Boolean(required=True,description="Is the domain sub link only")
    mode = fields.Enum(DomainType,required=True,description="The domain type")
    cdn_ip = fields.String(description="The cdn ip")
    grpc = fields.Boolean(required=True,description="Is the domain grpc")
    servernames = fields.String(description="The servernames")
    show_domains = fields.List(fields.String(),desciption="The list of domains to show")

class ProxySchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    name = fields.String(required=True, description="The proxy name")
    enable = fields.Boolean(required=True,description="Is the proxy enabled")
    proto = fields.Enum(ProxyProto,required=True,description="The proxy protocol")
    l3 = fields.Enum(ProxyL3,required=True,description="The proxy l3")
    transport = fields.Enum(ProxyTransport,required=True,description="The proxy transport")
    cdn = fields.Enum(ProxyCDN,required=True,description="The proxy cdn")


class StrConfigSchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    key = fields.Enum(ConfigEnum,required=True,description="The config key")
    value = fields.String(required=True,description="The config value")

class BoolConfigSchema(Schema):
    child_unique_id = fields.String(description="The child's unique id")
    key = fields.Enum(ConfigEnum,required=True,description="The config key")
    value = fields.Boolean(required=True,description="The config value")

class RegisterDataSchema(Schema):
    users = fields.List(fields.Nested(UserSchema),required=True,description="The list of users")
    domains = fields.List(fields.Nested(DomainSchema),required=True,description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema),required=True,description="The list of proxies")
    admin_users = fields.List(fields.Nested(AdminSchema),required=True,description="The list of admin users")
    str_configs = fields.List(fields.Nested(StrConfigSchema),required=True,description="The list of string configs")
    bool_configs = fields.List(fields.Nested(BoolConfigSchema),required=True,description="The list of boolean configs")

class RegisterSchema(Schema):
    panel_data = fields.Nested(RegisterDataSchema,required=True,description="The child's data")
    unique_id = fields.String(required=True,description="The child's unique id")


class OutputUsersSchema(Schema):
    users = fields.List(fields.Nested(UserSchema),required=True,description="The list of users")
    admins = fields.List(fields.Nested(AdminSchema),required=True,description="The list of admin users")

class RegisterApi(MethodView):
    decorators = [hiddify.super_admin]
    @app.input(RegisterSchema,arg_name='data')
    @app.output(OutputUsersSchema)
    def put(self,data):
        unique_id = data['unique_id']

        # if not hconfig(ConfigEnum.is_parent):
        #     abort(400,"Not a parent")


        child = Child.query.filter(Child.unique_id==unique_id).first()
        if not child:
            child=Child(unique_id=unique_id)
            db.session.add(child)
            db.session.commit()
            child=Child.query.filter(Child.unique_id==unique_id).first()
        
        # parse panel data
        self.__parse_panel_data(data['panel_data'])
        try:
            hiddify.set_db_from_json(data['panel_data'],override_child_id=child.id,set_users=True,remove_domains=True)
        except Exception as err:
            abort(400,str(err))

        # make response
        res = self.__create_response()
        
        return res
    
    def __parse_panel_data(self,panel_data):
        # mix str_configs and bool_configs to in a list
        hiddify.mix_str_configs_and_bool_configs(panel_data)
    def __create_response(self):
        '''Create response for parent register api'''
        res = OutputUsersSchema()
        res.users = [u.to_schema() for u in User.query.all()]
        res.admins = [a.to_schema() for a in AdminUser.query.all()]

        return res