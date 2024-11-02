import json
import os

from .abstract_driver import DriverABS
from hiddifypanel.models import User, hconfig, ConfigEnum
from hiddifypanel.panel.run_commander import Command, commander
import redis


USERS_USAGE = "wg:users-usage"


class WireguardApi(DriverABS):
    def get_redis_client(self):
        if not hasattr(self, 'redis_client'):
            self.redis_client = redis.from_url(os.environ.get("REDIS_URI_SSH",""))

        return self.redis_client

    def is_enabled(self) -> bool:
        return hconfig(ConfigEnum.wireguard_enable)

    def __init__(self) -> None:
        super().__init__()

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
        usage_data = self.get_redis_client() .get(USERS_USAGE)
        if usage_data:
            return json.loads(usage_data)

        return {}

    def __sync_local_usages(self, users) -> dict:
        local_usage = self.__get_local_usage()
        wg_usage = self.__get_wg_usages()
        res = {}
        # remove local usage that is removed from wg usage
        for local_wg_pub in local_usage.copy().keys():
            if local_wg_pub not in wg_usage:
                del local_usage[local_wg_pub]
        uuid_map = {u.wg_pub: u for u in users}
        for wg_pub, wg_usage in wg_usage.items():
            user = uuid_map.get(wg_pub)
            uuid = user.uuid if user else None
            if not local_usage.get(wg_pub):
                local_usage[wg_pub] = {"uuid": uuid, "usage": wg_usage}
                continue
            res[wg_pub] = self.calculate_reset(local_usage[wg_pub]['usage'], wg_usage)
            local_usage[wg_pub] = {"uuid": uuid, "usage": wg_usage}

        self.get_redis_client().set(USERS_USAGE, json.dumps(local_usage))

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
        new_wg_pubs = set(usages.keys())
        old_usages = self.__get_local_usage()
        old_wg_pubs = set(old_usages.keys())
        enabled = {u['uuid']: 1 for u in old_usages.values()}
        not_included = new_wg_pubs - old_wg_pubs
        if not_included:
            users = User.query.filter(User.wg_pub.in_(not_included).all())
            for u in users:
                enabled[u.uuid] = 1

        return enabled

    def add_client(self, user):
        pass

    def remove_client(self, user):
        pass

    def get_all_usage(self, users, reset=True):
        if not hconfig(ConfigEnum.wireguard_enable):
            return {}
        all_usages = self.__sync_local_usages(users)
        res = {}
        for u in users:
            if use := all_usages.get(u.wg_pub):
                res[u] = use['up'] + use['down']
            else:
                res[u] = 0
        return res
