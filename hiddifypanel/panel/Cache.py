from redis_cache import RedisCache
import redis
try:
    redis_client = redis.from_url('unix:///opt/hiddify-config/other/redis/run.sock?db=0', decode_responses=True)
    cache = RedisCache(redis_client=redis_client)
except:
    cache = RedisCache(redis_client=None)
