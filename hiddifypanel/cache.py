from redis_cache import RedisCache
import redis
from pickle import dumps, loads
redis_client = redis.from_url('unix:///opt/hiddify-config/other/redis/run.sock?db=0')


# def exception_handler(**kwargs):
#     pass

# cache = RedisCache(redis_client=redis_client, exception_handler=exception_handler)
cache = RedisCache(redis_client=redis_client, prefix="h", serializer=dumps, deserializer=loads)
