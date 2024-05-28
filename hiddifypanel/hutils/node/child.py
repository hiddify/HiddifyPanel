from loguru import logger
import socket
from flask_babel import gettext as _
from strenum import StrEnum

from hiddifypanel.models import AdminUser, User, hconfig, ConfigEnum, ChildMode, Domain, Proxy, StrConfig, BoolConfig, Child, ChildMode
from hiddifypanel import hutils
from hiddifypanel.panel import hiddify
from hiddifypanel.panel import usage
from hiddifypanel.database import db
from hiddifypanel.cache import cache

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
    panel_data.hconfigs = [*[u.to_schema() for u in StrConfig.query.all()], *[u.to_schema() for u in BoolConfig.query.all()]]  # type: ignore
    register_data.panel_data = panel_data

    return register_data


class SyncFields(StrEnum):
    domains = 'domains'
    proxies = 'proxies'
    hconfigs = 'hconfigs'


def __get_sync_data_for_api(*fields: SyncFields) -> SyncInputSchema:
    sync_data = SyncInputSchema()
    if len(fields) == 0:
        sync_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
        sync_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
        sync_data.hconfigs = [*[u.to_schema() for u in StrConfig.query.all()], *[u.to_schema() for u in BoolConfig.query.all()]]  # type: ignore
    else:
        for f in fields:
            match f:
                case SyncFields.domains:
                    sync_data.domains = [domain.to_schema() for domain in Domain.query.all()]  # type: ignore
                case SyncFields.proxies:
                    sync_data.proxies = [proxy.to_schema() for proxy in Proxy.query.all()]  # type: ignore
                case SyncFields.hconfigs:
                    sync_data.hconfigs = [*[u.to_schema() for u in StrConfig.query.all()], *[u.to_schema() for u in BoolConfig.query.all()]]  # type: ignore

    return sync_data


def __get_parent_panel_url() -> str:
    url = 'https://' + f"{hconfig(ConfigEnum.parent_domain).removesuffix('/')}/{hconfig(ConfigEnum.parent_admin_proxy_path).removesuffix('/')}"
    return url

# endregion


def is_registered() -> bool:
    '''Checks if the current parent registered as a child'''
    try:
        logger.debug("Checking if current panel is registered with parent")
        base_url = __get_parent_panel_url()
        if not base_url:
            return False
        payload = ChildStatusInputSchema()
        payload.child_unique_id = hconfig(ConfigEnum.unique_id)

        res = NodeApiClient(base_url).post('/api/v2/parent/status/', payload, ChildStatusOutputSchema)
        if isinstance(res, NodeApiErrorSchema):
            logger.error(f"Error while checking if current panel is registered with parent: {res.msg}")
            return False

        if res['existance']:
            return True
        return False
    except Exception as e:
        logger.error(f"Error while checking if current panel is registered with parent")
        logger.exception(e)
        return False


def register_to_parent(name: str, apikey: str, mode: ChildMode = ChildMode.remote) -> bool:
    # get parent link its format is "https://panel.hiddify.com/<admin_proxy_path>/"
    p_url = __get_parent_panel_url()
    if not p_url:
        logger.error("Parent url is empty")
        return False

    payload = __get_register_data_for_api(name, mode)
    res = NodeApiClient(p_url, apikey).put('/api/v2/parent/register/', payload, RegisterOutputSchema)
    if isinstance(res, NodeApiErrorSchema):
        logger.error(f"Error while registering to parent: {res.msg}")
        return False

    # TODO: change the bulk_register and such methods to accept models instead of dict
    AdminUser.bulk_register(res['admin_users'], commit=False)
    User.bulk_register(res['users'], commit=False)

    # add new child as parent
    db.session.add(  # type: ignore
        Child(unique_id=res['parent_unique_id'], name=socket.gethostname() or res['parent_unique_id'], mode=ChildMode.parent)
    )

    db.session.commit()  # type: ignore

    logger.success("Successfully registered to parent")
    cache.invalidate_all_cached_functions()
    return True


def sync_with_parent(*fields: SyncFields) -> bool:
    # sync usage first
    if not sync_users_usage_with_parent():
        logger.error("Error while syncing with parent: Failed to sync users usage")
        return False

    p_url = __get_parent_panel_url()
    if not p_url:
        logger.error("Error while syncing with parent: Parent url is empty")
        return False
    payload = __get_sync_data_for_api(*fields)
    res = NodeApiClient(p_url).put('/api/v2/parent/sync/', payload, SyncOutputSchema)
    if isinstance(res, NodeApiErrorSchema):
        logger.error(f"Error while syncing with parent: {res.msg}")
        return False
    AdminUser.bulk_register(res['admin_users'], commit=False, remove=True)
    User.bulk_register(res['users'], commit=False, remove=True)
    db.session.commit()  # type: ignore
    logger.success("Successfully synced with parent")
    cache.invalidate_all_cached_functions()
    return True


def sync_users_usage_with_parent() -> bool:
    p_url = __get_parent_panel_url()
    if not p_url:
        logger.error("Parent url is empty")
        return False

    payload = hutils.node.get_users_usage_data_for_api()
    if payload:
        res = NodeApiClient(p_url).put('/api/v2/parent/usage/', payload, UsageInputOutputSchema)  # type: ignore
        if isinstance(res, NodeApiErrorSchema):
            logger.error(f"Error while syncing users usage with parent: {res.msg}")
            return False

        # parse usages data
        res = hutils.node.convert_usage_api_response_to_dict(res)  # type: ignore
        usage.add_users_usage_uuid(res, hiddify.get_child(None), True)
        logger.success(f"Successfully synced users usage with parent: {res}")

    return True
