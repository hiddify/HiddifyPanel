from flask import g
from flask_babel import lazy_gettext as _
from typing import List
from loguru import logger

from hiddifypanel.models import Child, AdminUser, ConfigEnum, Domain, hconfig, Domain
from hiddifypanel import hutils
from hiddifypanel.panel.commercial.restapi.v2.child.schema import RegisterWithParentInputSchema
from .api_client import NodeApiClient, NodeApiErrorSchema

from hiddifypanel.cache import cache


def request_childs_to_sync():
    for c in Child.query.filter(Child.id != 0).all():
        if not request_child_to_sync(c):
            logger.error(f'{c.name}: {_("parent.sync-req-failed")}')
            hutils.flask.flash(f'{c.name}: ' + _('parent.sync-req-failed'), 'danger') # just for debug


def request_child_to_sync(child: Child) -> bool:
    '''Requests to a child to sync itself with the current panel'''
    child_domain = Domain.get_panel_link(child.id)  # type:ignore
    if not child_domain:
        logger.error(f"Child {child.name} has no valid domain")
        return False

    child_admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin, child.id)
    base_url = f'https://{child_domain}/{child_admin_proxy_path}'
    path = '/api/v2/child/sync-parent/'
    res = NodeApiClient(base_url).post(path, payload=None, output=dict)
    if isinstance(res, NodeApiErrorSchema):
        logger.error(f"Error while requesting child {child.name} to sync: {res.msg}")
        return False
    if res['msg'] == 'ok':
        logger.success(f"Successfully requested child {child.name} to sync")
        cache.invalidate_all_cached_functions()
        return True

    logger.error(f"Request to child {child.name} to sync failed")
    return False

# before using this function should check child version


# TODO: not used
def request_chlid_to_register(name: str, child_link: str, apikey: str) -> bool:
    '''Requests to a child to register itself with the current panel'''
    if not child_link or not apikey:
        logger.error("Child link or apikey is empty")
        return False
    domain = Domain.get_panel_link()
    if not domain:
        logger.error("Domain is empty")
        return False
    from hiddifypanel.panel import hiddify

    payload = RegisterWithParentInputSchema()
    payload.parent_panel = hiddify.get_account_panel_link(AdminUser.by_uuid(g.account.uuid), domain)  # type: ignore
    payload.apikey = payload.name = hconfig(ConfigEnum.unique_id)

    logger.debug(f"Requesting child {name} to register")
    res = NodeApiClient(child_link, apikey).post('/api/v2/child/register-parent/', payload, dict)
    if isinstance(res, NodeApiErrorSchema):
        logger.error(f"Error while requesting child {name} to register: {res.msg}")
        return False

    if res['msg'] == 'ok':
        logger.success(f"Successfully requested child {name} to register")
        cache.invalidate_all_cached_functions()
        return True

    logger.error(f"Request to child {name} to register failed")
    return False


def is_child_domain_active(child: Child, domain: Domain) -> bool:
    '''Checks whether a child's domain is responsive'''
    if not domain.need_valid_ssl:
        return False
    child_admin_proxy_path = hconfig(ConfigEnum.proxy_path_admin, child.id)
    if not child_admin_proxy_path:
        return False

    return hutils.node.is_panel_active(domain.domain, child_admin_proxy_path)


def get_child_active_domains(child: Child) -> List[Domain]:
    actives = []
    for d in child.domains:  # type: ignore
        if is_child_domain_active(child, d):
            actives.append(d)
    return actives


def is_child_active(child: Child) -> bool:
    for d in child.domains:  # type: ignore
        if is_child_domain_active(child, d):
            return True
    return False
