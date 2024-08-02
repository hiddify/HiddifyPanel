from typing import List, Tuple
from flask import current_app, flash as flask_flash, g, request
from wtforms.validators import ValidationError
from apiflask import abort as apiflask_abort
from flask_babel import gettext as _
from flask import url_for  # type: ignore
from flask import abort as flask_abort
from markupsafe import Markup
from urllib.parse import urlparse
from strenum import StrEnum

import user_agents
import re
import os

from hiddifypanel.cache import cache
from hiddifypanel.models import *
from hiddifypanel import hutils


def flash(message: str, category: str = "message"):
    if not isinstance(message, str):
        message = str(message)
    return flask_flash(message, category)


def flash_config_success(restart_mode: ApplyMode = ApplyMode.nothing, domain_changed=True):
    if restart_mode != ApplyMode.nothing:
        url = hurl_for('admin.Actions:reinstall', complete_install=restart_mode == ApplyMode.reinstall, domain_changed=domain_changed)
        apply_btn = f"<a href='{url}' class='btn btn-primary form_post'>" + \
            _("admin.config.apply_configs") + "</a>"
        flash((_('config.validation-success', link=apply_btn)), 'success')  # type: ignore
    else:
        flash((_('config.validation-success-no-reset')), 'success')  # type: ignore


def static_url_for(**values):
    orig = url_for("static", **values)
    return orig.split("user_secret")[0]


def hurl_for(endpoint, **values):
    if Child.current().id != 0:

        new_endpoint = "child_" + endpoint
        if new_endpoint in current_app.view_functions:
            endpoint = new_endpoint
    return url_for(endpoint, **values)


def get_user_agent() -> dict:
    ua = __parse_user_agent(request.user_agent.string)

    if ua.get('v', 1) < 7:
        __parse_user_agent.invalidate_all()  # type:ignore
        ua = __parse_user_agent(request.user_agent.string)
    return ua


ua_version_pattern = re.compile(r'/(\d+\.\d+(\.\d+)?)')


@cache.cache()
def __parse_user_agent(ua: str) -> dict:
    # Example: SFA/1.8.0 (239; sing-box 1.8.0)
    # Example: SFA/1.7.0 (239; sing-box 1.7.0)
    # Example: HiddifyNext/0.13.6 (android) like ClashMeta v2ray sing-box

    uaa = user_agents.parse(ua)

    match = re.search(ua_version_pattern, ua)
    generic_version = list(map(int, match.group(1).split('.'))) if match else [0, 0, 0]
    res = {}
    res['v'] = 7
    res["is_bot"] = uaa.is_bot
    res["is_browser"] = re.match('^Mozilla', ua, re.IGNORECASE) and True
    res['os'] = uaa.os.family
    res['os_version'] = uaa.os.version
    res['is_clash'] = re.match('^(Clash|Stash)', ua, re.IGNORECASE) and True
    res['is_clash_meta'] = re.match('^(Clash-verge|Clash-?Meta|Stash|NekoBox|NekoRay|Pharos|hiddify-desktop)', ua, re.IGNORECASE) and True
    res['is_singbox'] = re.match('^(HiddifyNext|Dart|SFI|SFA)', ua, re.IGNORECASE) and True
    res['is_hiddify'] = re.match('^(HiddifyNext)', ua, re.IGNORECASE) and True
    res['is_streisand'] = re.match('^(Streisand)', ua, re.IGNORECASE) and True
    res['is_shadowrocket'] = re.match('^(Shadowrocket)', ua, re.IGNORECASE) and True
    res['is_v2rayng'] = re.match('^(v2rayNG)', ua, re.IGNORECASE) and True

    if res['is_v2rayng']:
        res['v2rayng_version'] = generic_version
    if res['is_singbox']:
        res['singbox_version'] = generic_version

    if res['is_hiddify']:
        res['hiddify_version'] = generic_version
        if generic_version[0] == 0 and generic_version[1] <= 14:
            res['singbox_version'] = [1, 7, 0]
        else:
            res['singbox_version'] = [1, 8, 0]

    res['is_v2ray'] = re.match('^(Hiddify|FoXray|Fair|v2rayNG|SagerNet|Shadowrocket|V2Box|Loon|Liberty)', ua, re.IGNORECASE) and True

    if res['os'] == 'Other':
        if re.match('^(FoXray|Fair|Shadowrocket|V2Box|Loon|Liberty)', ua, re.IGNORECASE):
            res['os'] = 'iOS'
            # res['os_version']

    for a in ['Hiddify', 'FoXray', 'Fair', 'v2rayNG', 'SagerNet', 'Shadowrocket', 'V2Box', 'Loon', 'Liberty', 'Clash', 'Meta', 'Stash', 'SFI', 'SFA', 'HiddifyNext']:
        if a.lower() in ua.lower():
            res['app'] = a
    if res["is_browser"]:
        res['app'] = uaa.browser.family
    return res


def get_proxy_path_from_url(url: str) -> str | None:
    url_path = urlparse(url).path
    proxy_path = url_path.lstrip('/').split('/')[0] or None
    return proxy_path


def is_api_call(req_path: str) -> bool:
    return 'api/v1/' in req_path or 'api/v2/' in req_path


def is_user_api_call() -> bool:
    if request.blueprint and request.blueprint == 'api_user':
        return True
    user_api_call_format = '/api/v2/user/'
    if user_api_call_format in request.path:
        return True
    return False


def is_user_panel_call(deprecated_format=False) -> bool:
    if request.blueprint and request.blueprint == 'client':
        return True
    if deprecated_format:
        user_panel_url = f'/{hconfig(ConfigEnum.proxy_path)}/'
    else:
        user_panel_url = f'/{hconfig(ConfigEnum.proxy_path_client)}/'
    if f'{request.path}'.startswith(user_panel_url) and "admin" not in f'{request.path}':
        return True
    return False


def is_admin_panel_call(deprecated_format: bool = False) -> bool:
    if request.blueprint and request.blueprint == 'admin':
        return True
    if deprecated_format:
        if f'{request.path}'.startswith(f'/{hconfig(ConfigEnum.proxy_path)}/') and "admin" in f'{request.path}':
            return True
    elif f'{request.path}'.startswith(f'/{hconfig(ConfigEnum.proxy_path_admin)}/admin/'):
        return True
    return False


def is_api_v1_call(endpoint=None) -> bool:
    if (request.blueprint and 'api_v1' in request.blueprint):
        return True
    elif endpoint and 'api_v1' in endpoint:
        return True
    elif request.endpoint and 'api_v1' in request.endpoint:
        return True

    api_v1_path = f'{request.host}/{hconfig(ConfigEnum.proxy_path_admin)}/api/v1/{AdminUser.get_super_admin_uuid()}/'
    if f'{request.host}{request.path}'.startswith(api_v1_path):
        return True
    return False


def is_login_call() -> bool:
    return request.blueprint == 'common_bp'


def is_admin_role(role: Role) -> bool:
    if not role:
        return False
    if role in {Role.super_admin, Role.admin, Role.agent}:
        return True
    return False


def is_admin_proxy_path() -> bool:
    proxy_path = g.get('proxy_path') or get_proxy_path_from_url(request.url)
    return proxy_path in [hconfig(ConfigEnum.proxy_path_admin)] or (proxy_path in [hconfig(ConfigEnum.proxy_path)] and "/admin/" in request.path)


def is_client_proxy_path() -> bool:
    proxy_path = g.get('proxy_path') or get_proxy_path_from_url(request.url)
    return proxy_path in [hconfig(ConfigEnum.proxy_path_client)] or (proxy_path in [hconfig(ConfigEnum.proxy_path)] and "/admin/" not in request.path)


def __is_admin_api_call() -> bool:
    if request.blueprint and request.blueprint == 'api_admin' or request.blueprint == 'api_v1':
        return True
    admin_api_call_format = '/api/v2/admin/'
    if admin_api_call_format in request.path:
        return True
    return False


def proxy_path_validator(proxy_path: str) -> None:
    # DEPRECATED PROXY_PATH HANDLED BY BACKWARD COMPATIBILITY MIDDLEWARE
    # does not nginx handle proxy path validation?

    if not proxy_path:
        return apiflask_abort(400, 'invalid request')

    dbg_mode = True if current_app.config['DEBUG'] else False
    admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin)
    client_proxy_path = hconfig(ConfigEnum.proxy_path_client)
    deprecated_path = hconfig(ConfigEnum.proxy_path)
    if proxy_path == deprecated_path:
        return

    if proxy_path not in [admin_proxy_path, deprecated_path, client_proxy_path]:
        apiflask_abort(400, 'invalid request')

    if is_admin_panel_call() and proxy_path != admin_proxy_path:
        apiflask_abort(400, 'invalid request')
    if is_user_panel_call() and proxy_path != client_proxy_path:
        apiflask_abort(400, 'invalid request')

    if is_api_call(request.path):
        if __is_admin_api_call() and proxy_path != admin_proxy_path:
            return flask_abort(400, Markup(f"Invalid Proxy Path <a href=/{admin_proxy_path}/admin>Admin Panel</a>")) if dbg_mode else apiflask_abort(400, 'invalid request')
        if is_user_api_call() and proxy_path != client_proxy_path:
            return flask_abort(400, Markup(f"Invalid Proxy Path <a href=/{client_proxy_path}/admin>User Panel</a>")) if dbg_mode else apiflask_abort(400, 'invalid request')


def list_dir_files(dir_path: str) -> List[str]:
    return sorted([f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))])


def validate_domain_exist(form, field):
    domain = field.data
    if not domain:
        return
    dip = hutils.network.get_domain_ip(domain)
    if dip is None:
        raise ValidationError(
            _("Domain can not be resolved! there is a problem in your domain"))  # type: ignore


def get_proxy_stats_url():
    proxy_stats_url = f'{request.host_url}{g.proxy_path}/proxy-stats/'
    params = f'hostname={proxy_stats_url}api/&port=443&secret=hiddify'
    return f'{proxy_stats_url}?{params}'


def extract_parent_info_from_url(url) -> Tuple[str | None, str | None, str | None]:
    pattern = r'^https?://([^/]+)/([^/]+)/([^/]+)/.*$'
    match = re.match(pattern, url)

    if match:
        domain = match.group(1)
        proxy_path = match.group(2)
        admin_uuid = match.group(3)
        return domain, proxy_path, admin_uuid
    else:
        return None, None, None


class ClientVersion(StrEnum):
    v2ryang = 'v2rayng_version'
    hiddify_next = 'hiddify_version'


def is_client_version(client: ClientVersion, major_v: int = 0, minor_v: int = 0, patch_v: int = 0) -> bool:
    '''If the user agent version be equals or higher than parameters returns True'''
    if raw_v := g.user_agent.get(client):
        # TODO: probably we don't need these checks and the compare_versions can handle it (need to be test)
        raw_v_len = len(raw_v)
        u_major_v = raw_v[0] if raw_v_len > 0 else 0
        u_minor_v = raw_v[1] if raw_v_len > 1 else 0
        u_patch_v = raw_v[2] if raw_v_len > 2 else 0

        user_agent_v = f'{u_major_v}.{u_minor_v}.{u_patch_v}'
        needed_version = f'{major_v}.{minor_v}.{patch_v}'

        res = hutils.utils.compare_versions(user_agent_v, needed_version)
        if res == 0 or res == 1:
            return True
    return False

# region not used


# def api_v1_auth(function):
#     def wrapper(*args, **kwargs):
#         a_uuid = kwargs.get('admin_uuid')
#         if not a_uuid or a_uuid != AdminUser.get_super_admin_uuid():
#             apiflask_abort(403, 'invalid request')
#         return function(*args, **kwargs)
#     return wrapper


# def current_account_api_key():
#     return g.account.uuid


# def current_account_user_pass() -> Tuple[str, str]:
#     return g.account.username, g.account.password


# def is_telegram_call() -> bool:
#     if request.endpoint and (request.endpoint == 'tgbot' or request.endpoint == 'send_msg'):
#         return True
#     if request.blueprint and request.blueprint == 'api_v1' and ('tgbot' in request.path or 'send_msg' in request.path):
#         return True
#     if '/tgbot/' in request.path or 'send_msg/' in request.path:
#         return True
#     return False


# def is_admin_home_call() -> bool:
#     admin_home = f'{request.host}/{hconfig(ConfigEnum.proxy_path_admin)}/admin/'
#     if f'{request.host}{request.path}' == admin_home:
#         return True
#     return False


# def asset_url(path) -> str:
#     return f"/{g.proxy_path}/{path}"
# endregion
