from enum import auto
from strenum import StrEnum
from hiddifypanel.models.admin import AdminUser
from hiddifypanel.models.config import BoolConfig, StrConfig, hconfig
from hiddifypanel.models.config_enum import ConfigEnum
from hiddifypanel.models.domain import Domain
from hiddifypanel.models.proxy import Proxy
from hiddifypanel.models.user import User
from hiddifypanel.panel import hiddify
from hiddifypanel.panel.commercial.restapi.v2.parent.register_api import RegisterDataSchema, RegisterSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.sync_api import SyncDataSchema, SyncSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.usage_api import UsageDataSchema, UsageSchema, get_users_usage_info_for_api
import requests


class GetPanelDataForApi(StrEnum):
    register = auto()
    sync = auto()
    usage = auto()

def get_panel_data_for_api(type:GetPanelDataForApi) -> dict:
    if type == GetPanelDataForApi.register:
        res = RegisterSchema()
        res.unique_id = hconfig(ConfigEnum.unique_id)

        res.panel_data = RegisterDataSchema()
        res.panel_data.admin_users = [admin_user.to_schema() for admin_user in AdminUser.query.all()]
        res.panel_data.users = [user.to_schema() for user in User.query.all()]
        res.panel_data.domains = [domain.to_schema() for domain in Domain.query.all()]
        res.panel_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]
        res.panel_data.str_configs = [str_config.to_schema() for str_config in StrConfig.query.all()]
        res.panel_data.bool_configs = [bool_config.to_schema() for bool_config in BoolConfig.query.all()]

        return res.dump(res)
    elif type == GetPanelDataForApi.sync:
        res = SyncSchema()
        res.unique_id = hconfig(ConfigEnum.unique_id)
        res.panel_data = SyncDataSchema()
        res.panel_data.domains = [domain.to_schema() for domain in Domain.query.all()]
        res.panel_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]
        res.panel_data.str_configs = [str_config.to_schema() for str_config in StrConfig.query.all()]
        res.panel_data.bool_configs = [bool_config.to_schema() for bool_config in BoolConfig.query.all()]

        return res.dump(res)
    else:
        res = UsageSchema()
        res.unique_id = hconfig(ConfigEnum.unique_id)
        res.users_info = [UsageDataSchema.from_dict(item) for item in get_users_usage_info_for_api()]
        return res.dump(res)
    
def add_user_usage_to_parent(set_db=True):
    p_link = hconfig(ConfigEnum.parent_panel)
    if not p_link:
        return False
    # make proper panel api link
    p_link = p_link.removesuffix('/') + '/api/v2/parent/usage/'

    # make payload
    payload = get_panel_data_for_api(GetPanelDataForApi.usage)

    # send request to parent
    res = requests.put(p_link,json=payload)
    if res.status_code != 200:
        return False

    if set_db:
        # parse parent response to get users
        users_info:dict = res.json()
        data = {'users':[]}
        for u in users_info:
            dbuser = User.by_uuid(u['uuid'])
            dbuser.current_usage = u['usage']
            #TODO: check adding connected_ips
            dbuser.ips = u['connected_ips']
            data['users'].append(dbuser.to_dict())

        hiddify.set_db_from_json(data,set_users=True)
        
    return True

def sync_child_to_parent(set_db=True):
    
    p_link = hconfig(ConfigEnum.parent_panel)
    if not p_link:
        return False

    # make proper panel api link
    p_link = p_link.removesuffix('/') + '/api/v2/parent/sync/'

    # get panel data to use in api call
    payload = get_panel_data_for_api(GetPanelDataForApi.sync)
    
    # send request to parent
    res = requests.put(p_link, json=payload)
    if res.status_code != 200:
        return False
    
    if set_db:
        # parse parent response to get users
        res = res.json()
        hiddify.set_db_from_json(res,set_admins=True,set_users=True)
    return True


def register_child_to_parent(set_db=True) -> bool:
    # get parent link its format is "https://panel.hiddify.com/<proxy_path>/<uuid>/"
    p_link = hconfig(ConfigEnum.parent_panel)
    if not p_link:
        return False
    # make proper panel api link
    p_link = p_link.removesuffix('/') + '/api/v2/parent/register/'

    # get panel data to use in api call
    payload = get_panel_data_for_api(GetPanelDataForApi.register)

    # send request to parent
    res = requests.put(p_link, json=payload)
    if res.status_code != 200:
        return False
    
    if set_db:
        # parse parent response to get users
        res = res.json()
        hiddify.set_db_from_json(res,set_admins=True,set_users=True)

    return True