
from sqlalchemy.orm import Load, joinedload
from .ssh_liberty_bridge_api import SSHLibertyBridgeApi
from .xray_api import XrayApi
from .singbox_api import SingboxApi
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
drivers = [XrayApi(), SingboxApi(), SSHLibertyBridgeApi()]


def get_users_usage(reset=True):
    res = {}
    for user in User.query.all():
        d = 0
        for driver in drivers:
            try:
                d += driver.get_usage(user.uuid, reset=True) or 0
            except Exception as e:
                hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in get_usage for user={user.uuid}')
        res[user] = {'usage': d, 'ips': ''}
    return res


def get_enabled_users():
    from collections import defaultdict
    d = defaultdict(int)
    total = 0
    for driver in drivers:
        try:
            for u, v in driver.get_enabled_users().items():
                if not v:
                    continue
                d[u] += 1
            total += 1
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error in get_enabled users')

    res = defaultdict(bool)
    for u, v in d.items():
        res[u] = v >= total  # ignore singbox
    return res


def add_client(user):
    for driver in drivers:
        try:
            driver.add_client(user)
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in add client for user={user.uuid}')


def remove_client(user):
    for driver in drivers:
        try:
            driver.remove_client(user)
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in remove client for user={user.uuid}')
