from .ssh_liberty_bridge_api import SSHLibertyBridgeApi
from .xray_api import XrayApi
from .singbox_api import SingboxApi
from .wireguard_api import WireguardApi
from hiddifypanel.models import *
from hiddifypanel.panel import hiddify
from collections import defaultdict
from loguru import logger

drivers = [XrayApi(), SingboxApi(), SSHLibertyBridgeApi(), WireguardApi()]


def enabled_drivers():
    return [d for d in drivers if d.is_enabled()]


def get_users_usage(reset=True):
    res = {}
    users = list(User.query.all())
    res = defaultdict(lambda: {'usage': 0, 'devices': ''})
    for driver in enabled_drivers():
        try:
            all_usage = driver.get_all_usage(users)
            for user, usage in all_usage.items():
                if usage:
                    res[user]['usage'] += usage
                # res[user]['devices'] +=usage
        except Exception as e:
            print(driver)
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error in update usage {e}')
            logger.exception(f'ERROR! {driver.__class__.__name__} has error in update usage {e}')
    return res


def get_enabled_users():
    from collections import defaultdict
    d = defaultdict(int)
    total = 0
    for driver in enabled_drivers():
        try:
            for u, v in driver.get_enabled_users().items():
                # print(u, "enabled", v, driver)
                if not v:
                    continue
                d[u] += 1
            total += 1
        except Exception as e:
            print(driver)
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error in get_enabled users {e}')
            logger.exception(f'ERROR! {driver.__class__.__name__} has error in get_enabled users {e}')
    # print(d, total)
    res = defaultdict(bool)
    for u, v in d.items():
        # res[u] = v >= total  # ignore singbox
        res[u] = v >= 1
    return res


def add_client(user: User):
    for driver in enabled_drivers():
        try:
            driver.add_client(user)
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in add client for user={user.uuid} {e}')
            logger.exception(f'ERROR! {driver.__class__.__name__} has error {e} in add client for user={user.uuid} {e}')


def remove_client(user: User):
    for driver in enabled_drivers():
        try:
            driver.remove_client(user)
        except Exception as e:
            hiddify.error(f'ERROR! {driver.__class__.__name__} has error {e} in remove client for user={user.uuid}')
            logger.exception(f'ERROR! {driver.__class__.__name__} has error {e} in remove client for user={user.uuid}')
