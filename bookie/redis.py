import redis


def get_client(self):
    return redis.Redis()
