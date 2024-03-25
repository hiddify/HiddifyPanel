from .abstract_driver import DriverABS
from hiddifypanel.models import *
import redis

USERS_SET = "ssh-server:users"
USERS_USAGE = "ssh-server:users-usage"


class SSHLibertyBridgeApi(DriverABS):
    def is_enabled(self) -> bool:
        return hconfig(ConfigEnum.ssh_server_enable)

    def get_ssh_redis_client(self):
        if not hasattr(self, 'redis_client'):
            self.redis_client = redis.from_url('unix:///opt/hiddify-manager/other/redis/run.sock?db=1', decode_responses=True)

        return self.redis_client

    def get_enabled_users(self):
        redis_client = self.get_ssh_redis_client()
        members = redis_client.smembers(USERS_SET)
        return {m.split("::")[0]: 1 for m in members}

    def add_client(self, user):
        print(f'Adding SSH {user}')
        redis_client = self.get_ssh_redis_client()
        redis_client.sadd(USERS_SET, f'{user.uuid}::{user.ed25519_public_key}')
        redis_client.save()

    def remove_client(self, user):
        redis_client = self.get_ssh_redis_client()
        redis_client.srem(USERS_SET, f'{user.uuid}::{user.ed25519_public_key}')
        redis_client.hdel(USERS_USAGE, f'{user.uuid}')
        redis_client.save()

    def get_all_usage(self, users):
        return {u: self.get_usage_imp(u.uuid) for u in users}

    def get_usage_imp(self, client_uuid: str, reset: bool = True) -> int:
        redis_client = self.get_ssh_redis_client()
        value = redis_client.hget(USERS_USAGE, client_uuid)

        if value is None:
            return 0

        value = int(value)

        if reset:
            redis_client.hincrby(USERS_USAGE, client_uuid, -value)
            redis_client.save()
        if value:
            print(f'ssh usage {client_uuid} {value}')
        return value
