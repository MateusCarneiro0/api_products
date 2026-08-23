from redis import Redis

redis = Redis(host="localhost", port=6379, decode_responses=True)
redis.set("reids", "aaa", 10)
a = redis.get("reids")
print(a)
print("Deu certo")


def put_in_redis(key, acess_token):
    time_expires = 60 * 60 if acess_token else 7 * 24 * 60 * 60
    redis.set(key, "Invalid", time_expires)


def exists_in_redis(key):
    return redis.exists(key)
