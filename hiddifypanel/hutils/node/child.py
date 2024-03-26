from typing import Tuple, List
import requests
from enum import auto
from strenum import StrEnum


from hiddifypanel.models import AdminUser, User, hconfig, ConfigEnum, ChildMode
from hiddifypanel import hutils
from hiddifypanel.panel import hiddify
from hiddifypanel.panel import usage

# region private


class __ApiDataType(StrEnum):
    register = auto()
    sync = auto()
    usage = auto()


def __send_put_request_to_parent(url: str, payload: dict, key: str) -> dict:
    res = requests.put(url, json=payload, headers={'Hiddify-API-Key': key}, timeout=40)
    if res.status_code != 200:
        try:
            msg = res.json()
        except:
            msg = str(res.content)
        return {'err': {'code': res.status_code, 'msg': msg}}

    return res.json()


def __get_panel_data_for_api(type: __ApiDataType) -> dict | List[dict]:
    if type == __ApiDataType.register:
        register_data = RegisterDataSchema()  # type: ignore
        register_data.admin_users = [admin_user.to_schema() for admin_user in AdminUser.query.all()]  # type: ignore
        register_data.users = [user.to_schema() for user in User.query.all()]  # type: ignore
        register_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        register_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        register_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

        return register_data.dump(register_data)  # type: ignore
    elif type == __ApiDataType.sync:
        sync_data = SyncDataSchema()  # type: ignore
        sync_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        sync_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        sync_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

        return sync_data.dump(sync_data)  # type: ignore
    else:
        return hutils.node.get_users_usage_data_for_api()


def __get_parent_panel_info() -> Tuple[str, str]:
    return hconfig(ConfigEnum.parent_panel), hconfig(ConfigEnum.parent_unique_id)

# endregion


def is_child_registered() -> bool:
    '''Checks if the current parent registered as a child'''
    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/status/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id)
    }
    res = requests.post(p_url, json=payload, headers={'Hiddify-API-Key': p_key}, timeout=40)
    if res.status_code != 200:
        return False

    if res.json().get('existance') == True:
        return True

    return False


def register_to_parent(name: str, mode: ChildMode = ChildMode.remote, set_db=True) -> bool:
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
        'panel_data': __get_panel_data_for_api(__ApiDataType.register),
    }
    res = __send_put_request_to_parent(p_url, payload, p_key)
    if 'err' in res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False)
        User.bulk_register(res['users'], commit=False)
        db.session.commit()  # type: ignore

    return True


def sync_with_parent(set_db=True) -> bool:
    # sync usage first
    if not sync_users_usage_with_parent():
        return False

    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/sync/'

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'panel_data': __get_panel_data_for_api(__ApiDataType.sync)
    }

    res = __send_put_request_to_parent(p_url, payload, p_key)
    if 'err' in res:
        return False
    if set_db:
        AdminUser.bulk_register(res['admin_users'], commit=False, remove=True)
        User.bulk_register(res['users'], commit=False, remove=True)
        db.session.commit()  # type: ignore
    return True


def sync_users_usage_with_parent(set_db=True) -> bool:
    p_url, p_key = __get_parent_panel_info()
    if not p_url or not p_key:
        return False
    else:
        p_url = p_url.removesuffix('/') + '/api/v2/parent/usage/'

    # calculate usage increasement
    usage_payload = __get_panel_data_for_api(__ApiDataType.usage)

    payload = {
        'unique_id': hconfig(ConfigEnum.unique_id),
        'usages_data': usage_payload
    }

    res = __send_put_request_to_parent(p_url, payload, p_key)
    if 'err' in res:
        return False
    if set_db:
        # parse usages data
        res = convert_usage_api_response_to_dict(res)  # type: ignore
        usage.add_users_usage_uuid(res, hiddify.get_child(None), True)

    return True
