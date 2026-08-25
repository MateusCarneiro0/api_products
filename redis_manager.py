from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()

redis_port = int(os.getenv("REDIS_PORT", 6379))
redis_host = os.getenv("REDIS_URL", "localhost")

redis = Redis(host=redis_host, port=redis_port, decode_responses=True, db=0)

if redis.ping():
    print("REDIS CONNECTION SUCESSFULLY")
else:
    print("REDIS CONNECTION WRONG")


def put_in_redis(key, id, acess_token=False, time=0):
    time_expires = 60 * 60 if acess_token else 7 * 24 * 60 * 60
    ttl_seconds = time if time else time_expires
    token_type = "acess_token" if acess_token else "refresh_token"
    return redis.set(f"{token_type}:{id}:{key}", "Invalid", ex=ttl_seconds)


def exists_in_redis(key, id, is_acess_token=True):
    token_type = "acess_token" if is_acess_token else "refresh_token"
    return redis.exists(f"{token_type}:{id}:{key}")
