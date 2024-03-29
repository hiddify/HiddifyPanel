from redis_cache import RedisCache, CacheDecorator, compact_dump
from redis_cache import loads as redis_cache_loads
import redis
from pickle import dumps, loads
from loguru import logger

redis_client = redis.from_url('unix:///opt/hiddify-manager/other/redis/run.sock?db=0')


class CustomCacheDecorator(CacheDecorator):

    def __init__(self, *args, **kwargs):
        self.redis_cache = kwargs.pop('redis_cache')
        super().__init__(*args, **kwargs)

    def __call__(self, fn):
        new_fn = super().__call__(fn)
        self.redis_cache.cached_functions.append(new_fn)
        return new_fn


class CustomRedisCache(RedisCache):
    def __init__(self, redis_client, prefix="rc", serializer=compact_dump, deserializer=redis_cache_loads, key_serializer=None, exception_handler=None):
        super().__init__(redis_client, prefix, serializer, deserializer, key_serializer, exception_handler)
        self.cached_functions = []

    def cache(self, ttl=0, limit=0, namespace=None, exception_handler=None):
        return CustomCacheDecorator(
            redis_client=self.client,
            prefix=self.prefix,
            serializer=self.serializer,
            deserializer=self.deserializer,
            key_serializer=self.key_serializer,
            ttl=ttl,
            limit=limit,
            namespace=namespace,
            exception_handler=exception_handler or self.exception_handler,
            redis_cache=self
        )

    def invalidate_all_cached_functions(self):
        try:
            logger.info("Invalidating all cached functions")
            for cached_fn in self.cached_functions:
                cached_fn.invalidate_all()
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
