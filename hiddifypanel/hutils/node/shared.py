from typing import List
from hiddifypanel.models import hconfig, ConfigEnum, PanelMode, User
import requests
from hiddifypanel.panel.commercial.restapi.v2.parent.schema import UsageInputOutputSchema, UsageData
from hiddifypanel.panel.commercial.restapi.v2.panel.schema import PanelInfoOutputSchema
from .api_client import NodeApiClient, NodeApiErrorSchema


def is_child() -> bool:
    return hconfig(ConfigEnum.panel_mode) == PanelMode.child


def is_parent() -> bool:
    return hconfig(ConfigEnum.panel_mode) == PanelMode.parent

# region usage


def get_users_usage_data_for_api() -> UsageInputOutputSchema:
    res = UsageInputOutputSchema()
    res.usages = []  # type: ignore
    for u in User.query.all():
        usage_data = UsageData()
        usage_data.uuid = u.uuid
        usage_data.usage = u.current_usage
        usage_data.devices = u.devices
        res.usages.append(usage_data)  # type: ignore
    return res


def convert_usage_api_response_to_dict(data: dict) -> dict:
    converted = {}
    for i in data['usages']:  # type: ignore
        converted[str(i['uuid'])] = {
            'usage': i['usage'],
            'devices': ','.join(i['devices'])  # type: ignore
        }
    return converted

# endregion


def is_panel_active(domain: str, proxy_path: str, apikey: str) -> bool:
    base_url = f'https://{domain}/{proxy_path}'
    res = NodeApiClient(base_url, apikey).get('/api/v2/panel/ping/', dict)
    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return False
    if 'PONG' in res['msg']:
        return True
    return False


def get_panel_info(domain: str, proxy_path: str, apikey: str) -> dict | None:
    base_url = f'https://{domain}/{proxy_path}'
    res = NodeApiClient(base_url, apikey).get('/api/v2/panel/info/', PanelInfoOutputSchema)
    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return None
    return res
