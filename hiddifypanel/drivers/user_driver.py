from .ssh_liberty_bridge_api import SSHLibertyBridgeApi
from .xray_api import XrayApi
from .singbox_api import SingboxApi
from .wireguard_api import WireguardApi
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
drivers = [XrayApi(), SingboxApi(), SSHLibertyBridgeApi(), WireguardApi()]


def get_users_usage(reset=True):
    res = {}
    users = list(User.query.all())
    res = {u: {'usage': 0, 'ips': ''} for u in users}
    for driver in drivers:
        all_usage = driver.get_all_usage(users)
        for user, usage in all_usage.items():
            if usage:
                res[user]['usage'] += usage
            # res[user]['ip'] +=usage
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


def add_client(user: User):
    for driver in drivers:
        try:
            driver.add_client(user)
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in add client for user={user.uuid}')


def remove_client(user: User):
    for driver in drivers:
        try:
            driver.remove_client(user)
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in remove client for user={user.uuid}')
