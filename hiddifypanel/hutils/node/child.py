import requests

from hiddifypanel.models import AdminUser, User, hconfig, ConfigEnum, ChildMode, set_hconfig, Domain, Proxy, StrConfig, BoolConfig, Child, ChildMode
from hiddifypanel import hutils
from hiddifypanel.panel import hiddify
from hiddifypanel.panel import usage
from hiddifypanel.database import db

# import schmeas
from hiddifypanel.panel.commercial.restapi.v2.parent.schema import *
from hiddifypanel.panel.commercial.restapi.v2.child.schema import *

from .api_client import NodeApiClient, NodeApiErrorSchema
# region private


def __get_register_data_for_api(name: str, mode: ChildMode) -> RegisterInputSchema:

    register_data = RegisterInputSchema()
    register_data.unique_id = hconfig(ConfigEnum.unique_id)
    register_data.name = name  # type: ignore
    register_data.mode = mode  # type: ignore

    panel_data = RegisterDataSchema()  # type: ignore
    panel_data.admin_users = [admin_user.to_schema() for admin_user in AdminUser.query.all()]  # type: ignore
    panel_data.users = [user.to_schema() for user in User.query.all()]  # type: ignore
    panel_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
    panel_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
    panel_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore
    register_data.panel_data = panel_data

    return register_data


def __get_sync_data_for_api() -> SyncInputSchema:
    sync_data = SyncInputSchema()
    sync_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
    sync_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
    sync_data.hconfigs = [*[u.to_dict() for u in StrConfig.query.all()], *[u.to_dict() for u in BoolConfig.query.all()]]  # type: ignore

    return sync_data


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
    payload = {
        'child_unique_id': hconfig(ConfigEnum.unique_id)
    }
    res = requests.post(p_url, json=payload, headers={'Hiddify-API-Key': p_key}, timeout=3)
    if res.status_code != 200:
        return False

    if res.json().get('existance') == True:
        return True

    return False


def register_to_parent(name: str, mode: ChildMode = ChildMode.remote) -> bool:
    # get parent link its format is "https://panel.hiddify.com/<admin_proxy_path>/"
    p_url = __get_parent_panel_url()
    if not p_url:
        return False

    payload = __get_register_data_for_api(name, mode)
    apikey = hconfig(ConfigEnum.parent_admin_uuid)
    res = NodeApiClient(p_url, apikey).put('/api/v2/parent/register/', payload, RegisterOutputSchema)
    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return False

    # TODO: change the bulk_register and such methods to accept models instead of dict
    res = res.dump(res)  # convert to dict to insert/update
    set_hconfig(ConfigEnum.parent_unique_id, res.parent_unique_id)  # type: ignore
    AdminUser.bulk_register(res.admin_users, commit=False)
    User.bulk_register(res.users, commit=False)

    # add new child as parent
    db.session.add(  # type: ignore
        Child(unique_id=res.parent_unique_id, name=res.parent_unique_id, mode=ChildMode.parent)
    )
    db.session.commit()  # type: ignore

    return True


def sync_with_parent() -> bool:
    # sync usage first
    if not sync_users_usage_with_parent():
        return False

    p_url = __get_parent_panel_url()
    if not p_url:
        return False
    payload = __get_sync_data_for_api()
    res = NodeApiClient(p_url).put('/api/v2/parent/sync/', payload, SyncOutputSchema)
    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return False
    res = res.dump(res)
    AdminUser.bulk_register(res.admin_users, commit=False, remove=True)
    User.bulk_register(res.users, commit=False, remove=True)
    db.session.commit()  # type: ignore
    return True


def sync_users_usage_with_parent() -> bool:
    p_url = __get_parent_panel_url()
    if not p_url:
        return False

    payload = hutils.node.get_users_usage_data_for_api()
    res = NodeApiClient(p_url).put('/api/v2/parent/usage/', payload, UsageInputOutputSchema)  # type: ignore
    if isinstance(res, NodeApiErrorSchema):
        # TODO: log error
        return False

    # parse usages data
    res = hutils.node.convert_usage_api_response_to_dict(res)  # type: ignore
    usage.add_users_usage_uuid(res, hiddify.get_child(None), True)

    return True
