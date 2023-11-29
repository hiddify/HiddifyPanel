from apiflask import abort
from flask.views import MethodView
from hiddifypanel.models.config import hconfig
from flask import current_app as app
from hiddifypanel.models.user import User
from hiddifypanel.panel import hiddify
import requests
from hiddifypanel.models.config_enum import ConfigEnum


from hiddifypanel.panel.commercial.restapi.v2.parent.usage_api import UsageSchema, UsageDataSchema,get_users_usage_info_for_api



class UsageApi(MethodView):
    decorators = [hiddify.super_admin]
    def put(self):
        p_link = hconfig(ConfigEnum.parent_panel)
        if not p_link:
            abort(400,"The parent link is not set")
        # make proper panel api link
        p_link = p_link.removesuffix('/') + '/api/v2/parent/usage/'

        # make payload
        payload = self.__get_payload_for_api_call()
        # send request to parent
        res = requests.put(p_link,json=payload)
        if res.status_code != 200:
            abort(400,res.text)

        # parse parent response to get users
        users_info:dict = res.json()
        data = {'users':[]}
        for u in users_info:
            dbuser = User.by_uuid(u['uuid'])
            dbuser.current_usage = u['usage']
            #TODO: add connected_ips
            dbuser.ips = u['connected_ips']
            data['users'].append(dbuser.to_dict())

        hiddify.set_db_from_json(data,set_users=True)

        return {'message': 'ok'},200

    def __get_payload_for_api_call(self) -> dict:
        res = UsageSchema()
        res.unique_id = hconfig(ConfigEnum.unique_id)
        res.users_info = [UsageDataSchema.from_dict(item) for item in get_users_usage_info_for_api()]
        return res.dump(res)