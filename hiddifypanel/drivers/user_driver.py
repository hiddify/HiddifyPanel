

from . import ssh_liberty_bridge_api
from . import xray_api
from . import singbox_api


drivers = [xray_api(), singbox_api(), ssh_liberty_bridge_api()]


def get_users_usage(reset=True):
    res = {}
    for user in User.query.all():
        d = 0
        for driver in drivers:
            d += driver.get_usage(user.uuid, reset=True) or 0
        res[user] = {'usage': d, 'ips': ''}
    return res


def get_enabled_users(self):
    d = []
    for driver in drivers:
        d += driver.get_enabled_users() or []
    return d

def add_client(self,user):
    for driver in drivers:
        d += driver.add_client(user)
