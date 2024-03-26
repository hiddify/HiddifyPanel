from typing import List
from hiddifypanel.models import hconfig, ConfigEnum, PanelMode, User
import requests


def is_child() -> bool:
    if hconfig(ConfigEnum.panel_mode) == PanelMode.child:
        return True
    return False


def is_parent() -> bool:
    if hconfig(ConfigEnum.panel_mode) == PanelMode.parent:
        return True
    return False


# region usage

def get_users_usage_data_for_api() -> List[dict]:
    users = User.query.all()
    usages_data = [{'uuid': u.uuid, 'usage': u.current_usage, 'devices': u.ips} for u in users]
    return usages_data  # type: ignore


def convert_usage_api_response_to_dict(data: List[dict]) -> dict:
    converted = {}
    for i in data:
        converted[str(i['uuid'])] = {
            'usage': i['usage'],
            'devices': ','.join(i['devices']) if i['devices'] else ''
        }
    return converted

# endregion


def is_panel_active(domain: str, proxy_path: str, apikey: str) -> bool:
    api_url = 'https://'+f'{domain}/{proxy_path}/api/v2/ping/'.replace('//', '/')
    res = requests.get(api_url, headers={'Hiddify-API-Key': apikey}, timeout=2)
    if res.status_code == 200 and 'PONG' in res.json().get('msg'):
        return True
    return False
