from hiddifypanel.models import Domain, DomainType,Proxy,StrConfig,BoolConfig
from hiddifypanel.panel.commercial.restapi.v2.admin.user_api import UserSchema
import requests
from flask.views import MethodView
from apiflask import abort
from flask import current_app as app


from hiddifypanel.panel import hiddify
from hiddifypanel.models import hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from .register_api import ChildInputSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.sync_api import SyncSchema,SyncDataSchema


class SyncApi(MethodView):
    decorators = [hiddify.super_admin]

    @app.input(ChildInputSchema,arg_name='data')
    def put(self,data):
        p_link = data.get('parent_link') or hconfig(ConfigEnum.parent_panel)
        if not p_link:
            abort(400,"Parameter issue: 'The parent link is required'")

        # make proper panel api link
        p_link = p_link.removesuffix('/') + '/api/v2/parent/sync/'

        # get panel data to use in api call
        payload = self.__get_panel_data_for_api()
        
        # send request to parent
        res = requests.put(p_link, json=payload)
        if res.status_code != 200:
            abort(400,res.text)
            
        # parse parent response to get users
        res = res.json()
        hiddify.set_db_from_json(res,set_admins=True,set_users=True)
        return {'message':'ok'},200
    
    def __get_panel_data_for_api(self) -> dict:
        res = SyncSchema()
        res.unique_id = hconfig(ConfigEnum.unique_id)
        res.panel_data = SyncDataSchema()
        res.panel_data.domains = [domain.to_schema() for domain in Domain.query.all()]
        res.panel_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]
        res.panel_data.str_configs = [str_config.to_schema() for str_config in StrConfig.query.all()]
        res.panel_data.bool_configs = [bool_config.to_schema() for bool_config in BoolConfig.query.all()]

        return res.dump(res)
    def __modify_panel_data_for_api(self,panel_data):
        # remove unnecessary fields
        panel_data.pop('users',None)
        panel_data.pop('admin_users',None)
        panel_data.pop('parent_domains',None)

        # add sub_link_only field
        for d in panel_data['domains']:
            d['sub_link_only'] = True if d['mode'] == DomainType.sub_link_only else False

        #TODO: if we change the child_unique_id field value to panel unique_id(hconfig(ConfigEnum.unique_id)) in db, we need to remove this
        # fix child_unique_id field (convert its value to hconfig(ConfigEnum.unique_id))
        for item in panel_data['domains']:
            self.__fix_child_id_self_value(item)
        for item in panel_data['proxies']:
            self.__fix_child_id_self_value(item)
        for item in panel_data['hconfigs']:
            self.__fix_child_id_self_value(item)

        # convert hconfigs values to string
        for item in panel_data['hconfigs']:
            hiddify.convert_bool_to_string(item)
    
    def __fix_child_id_self_value(self,item):
        if item['child_unique_id'] == 'self':
            item['child_unique_id'] = hconfig(ConfigEnum.unique_id)