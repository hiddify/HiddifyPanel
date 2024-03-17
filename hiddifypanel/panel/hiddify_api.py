from enum import auto
from hiddifypanel.models.child import 
from strenum import StrEnum
from hiddifypanel.models import ChildMode,AdminUser,BoolConfig,StrConfig,hconfig,ConfigEnum,Domain,Proxy,User
from hiddifypanel.panel.commercial.restapi.v2.parent.register_api import RegisterDataSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.sync_api import SyncDataSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.usage_api import UsageDataSchema, get_users_usage_info_for_api
import requests


class GetPanelDataForApi(StrEnum):
    register = auto()
    sync = auto()
    usage = auto()


def get_panel_data_for_api(type: GetPanelDataForApi) -> dict:
    if type == GetPanelDataForApi.register:
        register_data = RegisterDataSchema()  # type: ignore
        register_data.admin_users = [admin_user.to_schema() for admin_user in AdminUser.query.all()]  # type: ignore
        register_data.users = [user.to_schema() for user in User.query.all()]  # type: ignore
        register_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        register_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        register_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

        return register_data.dump(register_data)  # type: ignore
    elif type == GetPanelDataForApi.sync:
        sync_data = SyncDataSchema()  # type: ignore
        sync_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        sync_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        sync_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

        return sync_data.dump(sync_data)  # type: ignore
    else:
        return [UsageDataSchema.from_dict(item) for item in get_users_usage_info_for_api()]  # type: ignore


def register_child_to_parent(name: str, mode: ChildMode, set_db=True) -> bool:

    # get parent link its format is "https://panel.hiddify.com/<admin_proxy_path>/<super_admin_uuid>/"
    if p_link := hconfig(ConfigEnum.parent_panel):
        p_link = p_link.removesuffix('/') + '/api/v2/parent/register/'
    else:
        return False

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'name': name,
        'mode': mode,
        'panel_data': get_panel_data_for_api(GetPanelDataForApi.register),
    }

    res = requests.put(p_link, json=payload)
    if res.status_code != 200:
        return False

    if set_db:
        res = res.json()
        # TODO: insert into db

    return True


def sync_child_with_parent(set_db=True) -> bool:
    if p_link := hconfig(ConfigEnum.parent_panel):
        p_link = p_link.removesuffix('/') + '/api/v2/parent/sync/'
    else:
        return False

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'panel_data': get_panel_data_for_api(GetPanelDataForApi.sync)
    }

    res = requests.put(p_link, json=payload)
    if res.status_code != 200:
        return False

    if set_db:
        res = res.json()
        # TODO: insert into db
    return True


def add_user_usage_to_parent(set_db=True) -> bool:
    raise NotImplementedError
    if p_link := hconfig(ConfigEnum.parent_panel):
        p_link = p_link.removesuffix('/') + '/api/v2/parent/usage/'
    else:
        return False

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'users_info': get_panel_data_for_api(GetPanelDataForApi.usage)
    }

    res = requests.put(p_link, json=payload)
    if res.status_code != 200:
        return False

    if set_db:
        # parse parent response to get users
        users_info: dict = res.json()
        data = {'users': []}
        for u in users_info:
            dbuser = User.by_uuid(u['uuid'])
            dbuser.current_usage = u['usage']
            # TODO: check adding connected_ips
            dbuser.ips = u['connected_ips']  # type: ignore
            data['users'].append(dbuser.to_dict())

        # TODO: insert into db

    return True
