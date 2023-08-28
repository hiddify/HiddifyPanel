from redis_cache import RedisCache
from functools import wraps
import redis
from pickle import dumps, loads
redis_client = redis.from_url('unix:///opt/hiddify-config/other/redis/run.sock?db=0')


def exception_handler(e, original_fn, args, kwargs):
    return original_fn(*args, **kwargs)
    pass


# cache = RedisCache(redis_client=redis_client, exception_handler=exception_handler)
# cache = RedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads, exception_handler=exception_handler)
cache = RedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads)


class CacheDecorator:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, fn):
        @wraps(fn)
        def inner(*args, **kwargs):

            parsed_result = fn(*args, **kwargs)

            return parsed_result

        inner.invalidate = self.invalidate
        inner.invalidate_all = self.invalidate_all
        inner.instance = self
        return inner

    def invalidate(self, *args, **kwargs):
        pass

    def invalidate_all(self, *args, **kwargs):
        pass


class DisableCache:
    cache = CacheDecorator


# cache = DisableCache()
try:
    @cache.cache()
    def test():
        return 1
    test()
except Exception as e:
    import sys
    print('Caching Error! Disabling cache', e, file=sys.stderr)
    cache = DisableCache()
