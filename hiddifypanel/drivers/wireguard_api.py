import json
import os

from .abstract_driver import DriverABS
from hiddifypanel.models import User, hconfig, ConfigEnum
from hiddifypanel.panel.run_commander import Command, commander


class WireguardApi(DriverABS):
    def is_enabled(self) -> bool:
        return hconfig(ConfigEnum.wireguard_enable)
    WG_LOCAL_USAGE_FILE_PATH = './hiddify_usages.json'

    def __init__(self) -> None:
        super().__init__()
        # create empty local usage file
        if not os.path.isfile(WireguardApi.WG_LOCAL_USAGE_FILE_PATH):
            with open(WireguardApi.WG_LOCAL_USAGE_FILE_PATH, 'w+') as f:
                json.dump({}, f)

    def __get_wg_usages(self) -> dict:
        raw_output = commander(Command.update_wg_usage, run_in_background=False)
        data = {}
        for line in raw_output.split('\n'):
            if not line:
                continue
            sections = line.split()
            if len(sections) < 3:
                continue
            data[sections[0]] = {
                'down': int(sections[1]),
                'up': int(sections[2]),
            }
        return data

    def __get_local_usage(self) -> dict:

        with open(WireguardApi.WG_LOCAL_USAGE_FILE_PATH, 'r') as f:
            data = json.load(f)
            return data

    def __sync_local_usages(self) -> dict:
        local_usage = self.__get_local_usage()
        wg_usage = self.__get_wg_usages()
        res = {}
        # remove local usage that is removed from wg usage
        for local_wg_pub in local_usage.copy().keys():
            if local_wg_pub not in wg_usage:
                del local_usage[local_wg_pub]

        for wg_pub, wg_usage in wg_usage.items():
            if not local_usage.get(wg_pub):
                local_usage[wg_pub] = wg_usage
                continue
            res[wg_pub] = self.calculate_reset(local_usage[wg_pub], wg_usage)
            local_usage[wg_pub] = wg_usage

        with open(WireguardApi.WG_LOCAL_USAGE_FILE_PATH, 'w') as f:
            json.dump(local_usage, f)
        return res

    def calculate_reset(self, last_usage: dict, current_usage: dict) -> dict:
        res = {
            'up': current_usage['up'] - last_usage['up'],
            'down': current_usage['down'] - last_usage['down'],
        }

        if res['up'] < 0:
            res['up'] = 0
        if res['down'] < 0:
            res['down'] = 0
        return res

    def get_enabled_users(self):
        if not hconfig(ConfigEnum.wireguard_enable):
            return {}
        usages = self.__get_wg_usages()
        wg_pubs = set(usages.keys())

        users = User.query.all()
        enabled = {}
        for u in users:
            if u.wg_pub in wg_pubs:
                enabled[u.uuid] = 1
            else:
                enabled[u.uuid] = 0
        return enabled

    def add_client(self, user):
        pass

    def remove_client(self, user):
        pass

    def get_all_usage(self, users, reset=True):
        if not hconfig(ConfigEnum.wireguard_enable):
            return {}
        all_usages = self.__sync_local_usages()
        res = {}
        for u in users:
            if use := all_usages.get(u.wg_pub):
                res[u] = use['up'] + use['down']
            else:
                res[u] = 0
        return res
