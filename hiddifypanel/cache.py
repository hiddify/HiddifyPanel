from redis_cache import RedisCache, CacheDecorator, compact_dump, chunks
from redis_cache import loads as redis_cache_loads
import redis
from pickle import dumps, loads
from loguru import logger

redis_client = redis.from_url('unix:///opt/hiddify-manager/other/redis/run.sock?db=0')


class CustomRedisCache(RedisCache):

    def invalidate_all_cached_functions(self):
        try:
            logger.info("Invalidating all cached functions")
            chunks_gen = chunks(f'{self.prefix}*', 500)
            for keys in chunks_gen:
                self.client.delete(*keys)
            logger.success("Successfully invalidated all cached functions")
            return True
        except Exception as err:
            with logger.contextualize(error=err):
                logger.error("Failed to invalidate all cached functions")
            return False


cache = CustomRedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads)


# cache = RedisCache(redis_client=redis_client, exception_handler=exception_handler)
# cache = RedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads, exception_handler=exception_handler)

# def exception_handler(e, original_fn, args, kwargs):
#     print("cache exception occur", e, original_fn, args, kwargs)
#     return original_fn(*args, **kwargs)
#     pass

# class CacheDecorator:
#     def __init__(self, *args, **kwargs):
#         pass

#     def __call__(self, fn):
#         @wraps(fn)
#         def inner(*args, **kwargs):

#             parsed_result = fn(*args, **kwargs)

#             return parsed_result

#         inner.invalidate = self.invalidate
#         inner.invalidate_all = self.invalidate_all
#         inner.instance = self
#         return inner

#     def invalidate(self, *args, **kwargs):
#         pass

#     def invalidate_all(self, *args, **kwargs):
#         pass


# class DisableCache:
#     cache = CacheDecorator


# cache = DisableCache()
# try:
#     @cache.cache()
#     def test():
#         return 1
#     test()
# except Exception as e:
#     import sys
#     print('Caching Error! Disabling cache', e, file=sys.stderr)
#     # cache = DisableCache()
