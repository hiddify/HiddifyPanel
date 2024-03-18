from strenum import StrEnum
from typing import Tuple
from enum import auto
import requests


from hiddifypanel.models import ChildMode, AdminUser, BoolConfig, StrConfig, hconfig, ConfigEnum, Domain, Proxy, User
from hiddifypanel.panel.commercial.restapi.v2.parent.register_api import RegisterDataSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.sync_api import SyncDataSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.usage_api import UsageDataSchema, get_users_usage_info_for_api
from hiddifypanel.database import db


class GetPanelDataForApi(StrEnum):
    register = auto()
    sync = auto()
    usage = auto()


def __get_parent_panel_info() -> Tuple[str, str]:
    return hconfig(ConfigEnum.parent_panel), hconfig(ConfigEnum.parent_api_key)


def __send_request_to_parent(url: str, payload: dict, key: str) -> dict:
    res = requests.put(url, json=payload, headers={'Hiddify-API-Key': key}, timeout=40)
    if res.status_code != 200:
        return {}

    return res.json()


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

    # get parent link its format is "https://panel.hiddify.com/<admin_proxy_path>/"
    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/register/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'name': name,
        'mode': mode,
        'panel_data': get_panel_data_for_api(GetPanelDataForApi.register),
    }
    res = __send_request_to_parent(p_url, payload, p_key)
    if not res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False)
        User.bulk_register(res['users'], commit=False)
        db.session.commit()  # type: ignore

    return True


def sync_child_with_parent(set_db=True) -> bool:
    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/sync/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'panel_data': get_panel_data_for_api(GetPanelDataForApi.sync)
    }

    res = __send_request_to_parent(p_url, payload, p_key)
    if not res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False)
        User.bulk_register(res['users'], commit=False)
        db.session.commit()  # type: ignore
    return True


def add_user_usage_to_parent(set_db=True) -> bool:
    raise NotImplementedError
    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/usage/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'users_info': get_panel_data_for_api(GetPanelDataForApi.usage)
    }

    __send_request_to_parent(p_url, payload, p_key)

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
