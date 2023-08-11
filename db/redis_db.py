import redis

from db.models import User
from utils.logger import logger

REDIS = "redis://localhost:6379"


class RedisAccess:
    def __init__(self):
        try:
            self.redis = redis.StrictRedis.from_url(REDIS, decode_responses=True)
            logger.info(f'Connected to database on: {REDIS}')
        except Exception as e:
            logger.error(f'Error while connecting to database: {e}')

    def save_users(self, users: list[User]) -> None:
        for user in users:
            if not self.redis.hgetall(f'{user.vk_id}-{user.group_url}'):
                user_map = {
                    "vk_id": user.vk_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "group_name": user.group_name,
                    "group_url": user.group_url
                }
                self.redis.hset(name=f'{user.vk_id}-{user.group_url}', mapping=user_map)



    def get_user_by_id(self, vk_id, group_url) -> dict | None:
        user_in_cache = self.redis.hgetall(f'{vk_id}-{group_url}')

        return user_in_cache

    def drop_all(self):
        logger.info(f"Кэш с пользователями был очищен")
        self.redis.flushall()

    def count_cache_users(self):
        return self.redis.dbsize()

