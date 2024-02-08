import subprocess
import json
import os

from .abstract_driver import DriverABS
from hiddifypanel.models import User


class WireguardApi(DriverABS):

    def __init__(self) -> None:
        super().__init__()
        self.local_usage_path = "./hiddify_usages.json"
        # create empty local usage file
        if not os.path.isfile(self.local_usage_path):
            with open(self.local_usage_path, 'w+') as f:
                json.dump({}, f)

    def __sync_local_usages(self):
        local_usage = self.__get_local_usage()
        wg_usage = self.__get_wg_usages()

        for wg_pub, wg_usage in wg_usage.items():
            if not local_usage.get(wg_pub):
                local_usage[wg_pub] = wg_usage
                continue

            # sync when item was not reseted
            if not local_usage[wg_pub].get('last_usage'):
                local_usage[wg_pub]['up'] = wg_usage['up']
                local_usage[wg_pub]['down'] = wg_usage['down']
            # sync item when was reseted
            else:
                last_usage = local_usage[wg_pub]['last_usage']
                local_usage[wg_pub]['up'] = wg_usage['up'] - last_usage['up']
                local_usage[wg_pub]['down'] = wg_usage['down'] - last_usage['down']

        with open(self.local_usage_path, 'w') as f:
            json.dump(local_usage, f)

    def __get_wg_usages(self) -> dict:
        raw_output = subprocess.check_output(['wg', 'show', 'hiddifywg', 'transfer'])
        data = {}
        for line in raw_output.decode('utf-8').split('\n'):
            if not line:
                continue
            sections = line.split()
            if len(sections) < 1:
                continue
            data[sections[0]] = {
                'down': int(sections[1]),
                'up': int(sections[2]),
            }
        return data

    def __get_local_usage(self) -> dict:

        with open(self.local_usage_path, 'r') as f:
            data = json.load(f)
            return data

    def __reset_local_usage_by_wg_pub(self, wg_pub: str) -> None:
        usages = self.__get_local_usage()
        if usages.get(wg_pub):
            usages[wg_pub] = {
                'up': 0,
                'down': 0,
                'last_usage': {
                    'up': usages[wg_pub].get('up', 0) + (usages[wg_pub]['last_usage']['up'] if 'last_usage' in usages[wg_pub] and 'up' in usages[wg_pub]['last_usage'] else 0),
                    'down': usages[wg_pub].get('down', 0) + (usages[wg_pub]['last_usage']['down'] if 'last_usage' in usages[wg_pub] and 'down' in usages[wg_pub]['last_usage'] else 0),
                }
            }
            with open(self.local_usage_path, 'w') as f:
                json.dump(usages, f)

    def __get_from_local_usage_by_wg_pub(self, wg_pub: str, reset: bool) -> dict | None:
        usages = self.__get_local_usage()
        if reset:
            self.__reset_local_usage_by_wg_pub(wg_pub)
        return usages.get(wg_pub, None)

    def get_enabled_users(self):
        self.__sync_local_usages()
        usages = self.__get_local_usage()
        wg_pubs = list(usages.keys())

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

    def get_usage(self, uuid, reset=True):
        user = User.by_uuid(uuid)
        if not user:
            raise Exception('the uuid not found during getting wg usage')
        wg_pub = user.wg_pub
        self.__sync_local_usages()
        user_usage = self.__get_from_local_usage_by_wg_pub(wg_pub, reset)
        if not user_usage:
            raise Exception('the wg pub not found during getting wg usage')
        up = user_usage.get('up')
        down = user_usage.get('down')

        res = None
        if down is None:
            res = up
        elif up is None:
            res = down
        else:
            res = down + up
        if res:
            print(f"Wireguard usage {uuid} d={down} u={up} sum={res}")
        return res
