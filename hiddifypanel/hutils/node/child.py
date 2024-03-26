from typing import Tuple, List
import requests
from enum import auto
from strenum import StrEnum

from hiddifypanel.models import AdminUser, User, hconfig, ConfigEnum, ChildMode, set_hconfig
from hiddifypanel import hutils
from hiddifypanel.panel import hiddify
from hiddifypanel.panel import usage

# region private


class __ApiDataType(StrEnum):
    register = auto()
    sync = auto()
    usage = auto()


def __send_put_request_to_parent(url: str, payload: dict, key: str) -> dict:
    res = requests.put(url, json=payload, headers={'Hiddify-API-Key': key}, timeout=10)
    if res.status_code != 200:
        try:
            msg = res.json()
        except:
            msg = str(res.content)
        return {'err': {'code': res.status_code, 'msg': msg}}

    return res.json()


def __get_panel_data_for_api(type: __ApiDataType) -> dict | List[dict]:
    if type == __ApiDataType.register:
        from hiddifypanel.panel.commercial.restapi.v2.parent.register_api import RegisterDataSchema
        register_data = RegisterDataSchema()  # type: ignore
        register_data.admin_users = [admin_user.to_schema() for admin_user in AdminUser.query.all()]  # type: ignore
        register_data.users = [user.to_schema() for user in User.query.all()]  # type: ignore
        register_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        register_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        register_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

        return register_data.dump(register_data)  # type: ignore
    elif type == __ApiDataType.sync:
        from hiddifypanel.panel.commercial.restapi.v2.parent.sync_api import SyncSchema
        sync_data = SyncSchema()  # type: ignore
        sync_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        sync_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        sync_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

        return sync_data.dump(sync_data)  # type: ignore
    else:
        return hutils.node.get_users_usage_data_for_api()


def __get_parent_panel_url() -> str:
    url = 'https://' + f"{hconfig(ConfigEnum.parent_domain).removesuffix('/')}/{hconfig(ConfigEnum.parent_admin_proxy_path).removesuffix('/')}"
    return url

# endregion


def is_child_registered() -> bool:
    '''Checks if the current parent registered as a child'''
    p_url = __get_parent_panel_url()
    if not p_url:
        return False
    else:
        p_url += '/api/v2/parent/status/'
    p_key = hconfig(ConfigEnum.parent_admin_uuid)
    res = requests.post(p_url, headers={'Hiddify-API-Key': p_key}, timeout=3)
    if res.status_code != 200:
        return False

    if res.json().get('existance') == True:
        return True

    return False


def register_to_parent(name: str, mode: ChildMode = ChildMode.remote, set_db=True) -> bool:
    # get parent link its format is "https://panel.hiddify.com/<admin_proxy_path>/"
    p_url = __get_parent_panel_url()
    if not p_url:
        return False
    else:
        p_url += '/api/v2/parent/register/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'name': name,
        'mode': mode,
        'panel_data': __get_panel_data_for_api(__ApiDataType.register),
    }
    p_key = hconfig(ConfigEnum.parent_admin_uuid)
    res = __send_put_request_to_parent(p_url, payload, p_key)
    if 'err' in res:
        return False
    if set_db:
        set_hconfig(ConfigEnum.parent_unique_id, res['parent_unique_id'])  # type: ignore
        AdminUser.bulk_register(res['admin_users'], commit=False)
        User.bulk_register(res['users'], commit=False)
        db.session.commit()  # type: ignore

    return True


def sync_with_parent(set_db=True) -> bool:
    # sync usage first
    if not sync_users_usage_with_parent():
        return False

    p_url = __get_parent_panel_url()
    if not p_url:
        return False
    else:
        p_url += '/api/v2/parent/sync/'

    payload = __get_panel_data_for_api(__ApiDataType.sync)

    res = __send_put_request_to_parent(p_url, payload, hconfig(ConfigEnum.unique_id))  # type: ignore
    if 'err' in res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False, remove=True)
        User.bulk_register(res['users'], commit=False, remove=True)
        db.session.commit()  # type: ignore
    return True


def sync_users_usage_with_parent(set_db=True) -> bool:
    p_url = __get_parent_panel_url()
    if not p_url:
        return False
    else:
        p_url += '/api/v2/parent/usage/'

    payload = __get_panel_data_for_api(__ApiDataType.usage)

    res = __send_put_request_to_parent(p_url, payload, hconfig(ConfigEnum.unique_id))  # type: ignore
    if 'err' in res:
        return False
    if set_db:
        # parse usages data
        res = hutils.node.convert_usage_api_response_to_dict(res)  # type: ignore
        usage.add_users_usage_uuid(res, hiddify.get_child(None), True)

    return True
