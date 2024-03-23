from flask import g
from hiddifypanel.models.child import Child
from hiddifypanel.models.domain import DomainType
from hiddifypanel.panel.usage import add_users_usage_uuid
from strenum import StrEnum
from typing import List, Tuple
from enum import auto
import requests


from hiddifypanel.models import ChildMode, AdminUser, BoolConfig, StrConfig, hconfig, ConfigEnum, Domain, Proxy, User
from hiddifypanel.panel.commercial.restapi.v2.parent.register_api import RegisterDataSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.sync_api import SyncDataSchema
from hiddifypanel.panel.commercial.restapi.v2.parent.usage_api import get_users_usage_data_for_api, convert_usage_api_response_to_dict
from hiddifypanel.database import db


# TODO: REFACTOR THIS FILE

class GetPanelDataForApi(StrEnum):
    register = auto()
    sync = auto()
    usage = auto()

# region private


def __get_parent_panel_info() -> Tuple[str, str]:
    return hconfig(ConfigEnum.parent_panel), hconfig(ConfigEnum.parent_api_key)


def __send_put_request_to_parent(url: str, payload: dict, key: str) -> dict:
    res = requests.put(url, json=payload, headers={'Hiddify-API-Key': key}, timeout=40)
    if res.status_code != 200:
        return {}

    return res.json()

# endregion


def get_panel_data_for_api(type: GetPanelDataForApi) -> dict | List[dict]:
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
        return get_users_usage_data_for_api()


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
    res = __send_put_request_to_parent(p_url, payload, p_key)
    if not res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False)
        User.bulk_register(res['users'], commit=False)
        db.session.commit()  # type: ignore

    return True


def sync_child_with_parent(set_db=True) -> bool:
    # sync usage first
    if not add_user_usage_to_parent():
        return False

    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/sync/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'panel_data': get_panel_data_for_api(GetPanelDataForApi.sync)
    }

    res = __send_put_request_to_parent(p_url, payload, p_key)
    if not res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False, remove=True)
        User.bulk_register(res['users'], commit=False, remove=True)
        db.session.commit()  # type: ignore
    return True


def add_user_usage_to_parent(set_db=True) -> bool:
    # TODO: decrease number of request
    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/usage/'

    # calculate usage increasement
    usage_payload = get_panel_data_for_api(GetPanelDataForApi.usage)

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'usages_data': usage_payload
    }

    res = __send_put_request_to_parent(p_url, payload, p_key)
    if not res:
        return False
    if set_db:
        # parse usages data
        res = convert_usage_api_response_to_dict(res)  # type: ignore
        add_users_usage_uuid(res, hconfig(ConfigEnum.unique_id), True)

    return True


def is_child_domain_active(child: Child, domain: Domain) -> bool:
    if domain.mode in [DomainType.reality, DomainType.fake]:
        return False
    api_key = g.account.uuid
    child_admin_proxy_path = StrConfig.query.filter(StrConfig.child_id == child.id, StrConfig.key == ConfigEnum.proxy_path_admin).first().value
    if not api_key or not child_admin_proxy_path:
        return False
    api_url = 'https://'+f'{domain.domain}/{child_admin_proxy_path}/api/v2/ping/'.replace('//', '/')
    res = requests.get(api_url, headers={'Hiddify-API-Key': api_key}, timeout=2)
    if res.status_code == 200 and 'PONG' in res.json().get('msg'):
        return True
    return False


def is_child_active(child: Child) -> bool:
    for d in child.domains:
        if d.mode in [DomainType.reality, DomainType.fake]:
            continue
        if is_child_domain_active(child, d):
            return True
    return False
