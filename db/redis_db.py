import redis

from config.config import get_config
from db.model import UserModel
from utils.logger import logger

config: dict = get_config()


class RedisAccess:
    __instance = None

    def __init__(self):
        if RedisAccess.__instance is not None:
            raise Exception("This redis class is a singleton!")
        else:
            RedisAccess.__instance = Redis()
            logger.info(f'Connected to database on: {config.get("redis_uri")}')

    @staticmethod
    def get_instance():
        if RedisAccess.__instance is None:
            RedisAccess()
        return RedisAccess.__instance


class Redis:
    def __init__(self):
        self._connection = redis.StrictRedis.from_url(config.get('redis_uri'), decode_responses=True)
        logger.info(f'Connected to database on: {config.get("redis_uri")}')

    def save_users(self, users: list[UserModel]) -> int:
        new_users_amount = 0
        for user in users:
            if not self._connection.hgetall(f'{user.vk_id}-{user.group_url}'):
                user_map = {
                    "vk_id": user.vk_id,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "group_name": user.group_name,
                    "group_url": user.group_url
                }
                self._connection.hset(name=f'{user.vk_id}-{user.group_url}', mapping=user_map)
                new_users_amount += 1
        return new_users_amount

    def get_user_by_id(self, vk_id, group_url) -> dict | None:
        user_in_cache = self._connection.hgetall(f'{vk_id}-{group_url}')

        return user_in_cache

    def drop_all(self):
        logger.info(f"Кэш с пользователями был очищен")
        self._connection.flushall()

    def count_cache_users(self):
        return self._connection.dbsize()

