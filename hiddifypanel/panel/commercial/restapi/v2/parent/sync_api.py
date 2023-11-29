
from flask.views import MethodView
#from hiddifypanel.panel.hiddify
from flask import current_app as app
from apiflask import abort,Schema,fields
from hiddifypanel.models.user import User
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.database import db
from hiddifypanel.models.child import Child
from hiddifypanel.models import *
from .register_api import DomainSchema, OutputUsersSchema,ProxySchema,StrConfigSchema,BoolConfigSchema


class SyncDataSchema(Schema):
    #users = fields.List(fields.Nested(UserSchema),required=True,description="The list of users")
    domains = fields.List(fields.Nested(DomainSchema),required=True,description="The list of domains")
    proxies = fields.List(fields.Nested(ProxySchema),required=True,description="The list of proxies")
    #parent_domains = fields.List(fields.Nested(ParentDomainSchema),required=True,description="The list of parent domains")
    #admin_users = fields.List(fields.Nested(AdminSchema),required=True,description="The list of admin users")
    str_configs = fields.List(fields.Nested(StrConfigSchema),required=True,description="The list of string configs")
    bool_configs = fields.List(fields.Nested(BoolConfigSchema),required=True,description="The list of boolean configs")

class SyncSchema(Schema):
    panel_data = fields.Nested(SyncDataSchema,required=False,description="The child's data")
    unique_id = fields.String(required=False,description="The child's unique id")

class SyncApi(MethodView):
    decorators = [hiddify.super_admin]
    @app.input(SyncSchema,arg_name='data')
    @app.output(OutputUsersSchema)
    def put(self,data):
        unique_id = data['unique_id']

        # if not hconfig(ConfigEnum.is_parent):
        #     abort(400,"Not a parent")


        child = Child.query.filter(Child.unique_id==unique_id).first()
        if not child:
            abort(400,"The child does not exist")

        if not child:
            child=Child(unique_id=unique_id)
            db.session.add(child)
            db.session.commit()
            child=Child.query.filter(Child.unique_id==unique_id).first()
        
        # parse panel data
        self.__parse_panel_data(data['panel_data'])
        try:
            hiddify.set_db_from_json(data['panel_data'],override_child_id=child.id,set_users=False,set_admins=False,remove_domains=True)
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