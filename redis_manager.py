from redis import Redis
from dotenv import load_dotenv
import os

load_dotenv()

redis_port = int(os.getenv("REDIS_PORT",6379))
redis_host = os.getenv("REDIS_URL","localhost")

redis = Redis(host=redis_host, port=redis_port, decode_responses=True)

def put_in_redis(key, acess_token=False,time=0):
    time_expires = 60 * 60 if acess_token else 7 * 24 * 60 * 60
    redis.set(key, "Invalid", time if time else time_expires)

def delete_in_redis(key):
    redis.delete(key)

def exists_in_redis(key):
    return redis.exists(key)
