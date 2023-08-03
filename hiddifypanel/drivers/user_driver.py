

from .ssh_liberty_bridge_api import SSHLibertyBridgeApi
from .xray_api import XrayApi
from .singbox_api import SingboxApi
from hiddifypanel.models import *

drivers = [XrayApi(), SingboxApi(), SSHLibertyBridgeApi()]


def get_users_usage(reset=True):
    res = {}
    for user in User.query.all():
        d = 0
        for driver in drivers:
            d += driver.get_usage(user.uuid, reset=True) or 0
        res[user] = {'usage': d, 'ips': ''}
    return res


def get_enabled_users():
    d = {}
    for driver in drivers:
        for u, v in driver.get_enabled_users().items():
            if not u in d or d[u]:
                d[u] = v
    return d


def add_client(user):
    for driver in drivers:
        d += driver.add_client(user)


def remove_client(user):
    for driver in drivers:
        d += driver.remove_client(user)
