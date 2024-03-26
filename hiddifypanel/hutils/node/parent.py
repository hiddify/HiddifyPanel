from flask import g
from flask_babel import lazy_gettext as _
import requests
from typing import List


from hiddifypanel import hutils
from hiddifypanel.models import Child, StrConfig, ConfigEnum, DomainType, Domain, ChildMode, hconfig, set_hconfig, PanelMode, get_panel_domains


def request_childs_to_sync():
    for c in Child.query.filter(Child.id != 0).all():
        if not request_child_to_sync(c):
            hutils.flask.flash(f'{c.name}: '+_('parent.sync-req-failed'), 'danger')


def request_child_to_sync(child: Child) -> bool:
    '''Requests to a child to sync itself with the current panel'''
    try:
        child_domain = get_child_active_domains(child)[0]
    except:
        return False
    child_admin_proxy_path = StrConfig.query.filter(StrConfig.child_id == child.id, StrConfig.key == ConfigEnum.proxy_path_admin).first().value
    url = f'https://{child_domain}/{child_admin_proxy_path}/api/v2/child/sync-parent/'
    res = requests.post(url, headers={'Hiddify-API-Key': hconfig(ConfigEnum.unique_id)})
    if res.status_code == 200 and res.json().get('msg') == 'ok':
        return True

    return False


def request_chlid_to_register(name: str, mode: ChildMode, child_link: str, child_key: str) -> bool:
    '''Requests to a child to register itself with the current panel'''
    if not child_link or not child_key:
        return False
    else:
        child_link = child_link.removesuffix('/') + '/api/v2/child/register-parent/'

    try:
        domain = get_panel_domains()[0].domain
    except:
        return False

    paylaod = {
        'parent_panel': f'https://{domain}/{hconfig(ConfigEnum.proxy_path_admin)}/{g.account.uuid}/',
        'name': name,
        'mode': mode

    }
    res = requests.post(child_link, json=paylaod, headers={'Hiddify-API-Key': hconfig(ConfigEnum.unique_id)}, timeout=40)
    if res.status_code == 200 and res.json().get('msg') == 'ok':
        set_hconfig(ConfigEnum.panel_mode, PanelMode.parent)  # type: ignore
        # don't need is_parent anymore, just for compatibility, it'll be deleted
        set_hconfig(ConfigEnum.is_parent, True)  # type: ignore
        return True

    return False


def is_child_domain_active(child: Child, domain: Domain) -> bool:
    '''Checks whether a child's domain is responsive'''
    if domain.mode in [DomainType.reality, DomainType.fake]:
        return False
    api_key = g.account.uuid
    child_admin_proxy_path = StrConfig.query.filter(StrConfig.child_id == child.id, StrConfig.key == ConfigEnum.proxy_path_admin).first().value
    if not api_key or not child_admin_proxy_path:
        return False

    return hutils.node.is_panel_active(domain.domain, child_admin_proxy_path, api_key)


def get_child_active_domains(child: Child) -> List[Domain]:
    actives = []
    for d in child.domains:
        if is_child_domain_active(child, d):
            actives.append(d)
    return actives


def is_child_active(child: Child) -> bool:
    for d in child.domains:
        if d.mode in [DomainType.reality, DomainType.fake]:
            continue
        if is_child_domain_active(child, d):
            return True
    return False


def get_childs_unique_id() -> List[str]:
    childs = Child.query.filter(Child.id != 0).all()
    return [c.unique_id for c in childs]
