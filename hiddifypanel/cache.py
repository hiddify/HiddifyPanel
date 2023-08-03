from redis_cache import RedisCache
import redis

redis_client = redis.from_url('unix:///opt/hiddify-config/other/redis/run.sock?db=0', decode_responses=True)


def exception_handler(**kwargs):
    pass


cache = RedisCache(redis_client=redis_client, exception_handler=exception_handler)
