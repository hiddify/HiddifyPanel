from .abstract_driver import DriverABS
from hiddifypanel.models import *
import redis

USERS_SET = "ssh-server:users"
USERS_USAGE = "ssh-server:users-usage"
from loguru import logger


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
        if user.ed25519_public_key is None:
            members = redis_client.smembers(USERS_SET)
            for member in members:
                if member.startswith(user.uuid):
                    redis_client.srem(USERS_SET, member)

        redis_client.srem(USERS_SET, f'{user.uuid}::{user.ed25519_public_key}')
        redis_client.hdel(USERS_USAGE, f'{user.uuid}')
        redis_client.save()

    def get_all_usage(self, users):
        redis_client = self.get_ssh_redis_client()
        allusage = redis_client.hgetall(USERS_USAGE)
        redis_client.delete(USERS_USAGE)
        return {u: int(allusage.get(u.uuid) or 0) for u in users}
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
            logger.debug(f'ssh usage {client_uuid} {value}')
        return value
