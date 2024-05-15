from redis_cache import RedisCache, chunks
import redis
from pickle import dumps, loads
from loguru import logger

redis_client = redis.from_url('unix:///opt/hiddify-manager/other/redis/run.sock?db=0')


class CustomRedisCache(RedisCache):

    def invalidate_all_cached_functions(self):
        try:
            logger.trace("Invalidating all cached functions")
            chunks_gen = chunks(f'{self.prefix}*', 500)
            for keys in chunks_gen:
                self.client.delete(*keys)
            logger.trace("Successfully invalidated all cached functions")
            return True
        except Exception as err:
            with logger.contextualize(error=err):
                logger.error("Failed to invalidate all cached functions")
            return False


cache = CustomRedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads)