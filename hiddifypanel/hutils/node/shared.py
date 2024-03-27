from typing import List
from hiddifypanel.models import hconfig, ConfigEnum, PanelMode, User
import requests


def is_child() -> bool:
    return hconfig(ConfigEnum.panel_mode) == PanelMode.child


def is_parent() -> bool:
    return hconfig(ConfigEnum.panel_mode) == PanelMode.parent

# region usage


def get_users_usage_data_for_api() -> List[dict]:
    users = User.query.all()
    usages_data = [{'uuid': u.uuid, 'usage': u.current_usage, 'devices': u.devices} for u in users]
    return usages_data  # type: ignore


def convert_usage_api_response_to_dict(data: List[dict]) -> dict:
    converted = {}
    for i in data:
        converted[str(i['uuid'])] = {
            'usage': i['usage'],
            'devices': ','.join(i['devices'])
        }
    return converted

# endregion


def is_panel_active(domain: str, proxy_path: str, apikey: str) -> bool:
    api_url = 'https://'+f'{domain}/{proxy_path}/api/v2/panel/ping/'.replace('//', '/')
    res = requests.get(api_url, headers={'Hiddify-API-Key': apikey}, timeout=2)
    if res.status_code == 200 and 'PONG' in res.json().get('msg'):
        return True
    return False


def get_panel_info(domain: str, proxy_path: str, apikey: str) -> dict:
    api_url = 'https://'+f'{domain}/{proxy_path}/api/v2/panel/info/'.replace('//', '/')
    res = requests.get(api_url, headers={'Hiddify-API-Key': apikey}, timeout=2)
    if res.status_code != 200:
        return {}
    return res.json()
