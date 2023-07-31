import logging
import redis

REDIS = "redis://localhost:6379"


class RedisAccess:
    def __init__(self):
        try:
            self.redis = redis.StrictRedis.from_url(REDIS, decode_responses=True)
            logging.info(f'Connected to database on: {REDIS}')
        except Exception as e:
            logging.error(f'Error while connecting to database: {e}')

    def save_users(self, user):
        pass

    def get_user(self):
        pass


