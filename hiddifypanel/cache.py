import os
from redis_cache import RedisCache, chunks, compact_dump
import redis
from pickle import dumps, loads
from loguru import logger
def get_env(key):
    from dotenv import dotenv_values
    for d,v in (dotenv_values("/opt/hiddify-manager/hiddify-panel/app.cfg") or {}).items():
        if key==d:return v

redis_client = redis.from_url(get_env("REDIS_URI_MAIN"))


class CustomRedisCache(RedisCache):
    def __init__(self, redis_client, prefix="rc", serializer=compact_dump, deserializer=loads, key_serializer=None, support_cluster=True, exception_handler=None):
        super().__init__(redis_client, prefix, serializer, deserializer, key_serializer, support_cluster, exception_handler)
        self.cached_functions = set()

    def cache(self, ttl=0, limit=0, namespace=None, exception_handler=None):
        res = super().cache(ttl, limit, namespace, exception_handler)
        self.cached_functions.add(res)
        return res

    def invalidate_all_cached_functions(self):
        try:
            for f in self.cached_functions:
                f.invalidate_all()
            logger.trace("Invalidating all cached functions")
            chunks_gen = chunks(f'{self.prefix}*', 5000)
            for keys in chunks_gen:
                self.client.delete(*keys)
            logger.trace("Successfully invalidated all cached functions")
            return True
        except Exception as err:
            with logger.contextualize(error=err):
                logger.error("Failed to invalidate all cached functions")
            return False


cache = CustomRedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads)
