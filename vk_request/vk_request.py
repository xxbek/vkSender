import logging
import time
from typing import Generator

import requests

from accounts.accounts import Account
from db.db import DBAccess
from db.models import User
from db.redis_db import RedisAccess
from utils.utils import get_all_valid_users


class VKRequest:
    def __init__(self, db: DBAccess, cache: RedisAccess, account: Account, delay=1):
        self._db = db
        self.cache = cache
        self._account = account
        self.delay = delay

    def sleep(self):
        time.sleep(self.delay)


class VKWriter(VKRequest):
    def __init__(self, db: DBAccess, cache: RedisAccess, account: Account, delay=1):
        super().__init__(db, cache, account, delay)

    def get_users_from_db(self) -> list:
        pass

    def write_to_the_user(self, user: User, message: str):
        self.sleep()
        response = requests.get('https://api.vk.com/method/messages.send', params={
            'access_token': self._account.access_token,
            'v': 5.103,
            'user_id': 287611673,
            'random_id': 1,
            'message': message + ' https://vk.com/cutebeawer',
            'dont_parse_links': 0,
        })

        if response.status_code == 200:
            logging.info(f"Сообщение было отправлено пользователю {user.vk_id}")

        self._db.change_user_message_status(user.vk_id)
        self._account.messages_written += 1

    def reply_to_unwritten_messages(self, second_messages: list[str]):
        pass


class VKSearcher(VKRequest):
    def __init__(self, db: DBAccess, cache: RedisAccess, account: Account, group_list: list[str], delay=1, caching=False):
        super().__init__(db, cache, account, delay)
        self.group_list = group_list
        self.caching = caching

    def get_group_offset(self, group_id):
        response = requests.get('https://api.vk.com/method/groups.getMembers', params={
            'access_token': self._account.access_token,
            'v': 5.103,
            'group_id': group_id,
            'sort': 'id_desc',
            'offset': 0,
            'fields': 'last_seen, can_write_private_message',
        }).json()

        if response.get('error'):
            err_message = response.get('error').get('error_msg')
            logging.error(f'Ошибка при поиске пользователей в группе `{group_id}`: {err_message}')
            return

        users = response['response']['count']

        return users // 1000

    def yield_users_from_groups(self) -> Generator:
        for group in self.group_list:
            for new_user in self.yield_users_from_one_group(group):
                yield new_user
            logging.info(f"Группа `{group}` была просканированна, найдено {len(new_user)} человек")

    def yield_users_from_one_group(self, group_id) -> Generator:
        filtered_users = []
        offset = 0
        max_offset = self.get_group_offset(group_id)
        while offset < max_offset:
            self.sleep()
            response = requests.get('https://api.vk.com/method/groups.getMembers', params={
                'access_token': self._account.access_token,
                'v': 5.103,
                'sort': 'id_desc',
                'group_id': group_id,
                'offset': offset * 1000,
                'fields': 'last_seen, can_write_private_message',
            }).json()['response']
            offset += 1

            if self.caching:
                all_valid_user: list = get_all_valid_users(response)
                filtered_users.extend(all_valid_user)
            else:
                all_valid_user: list = get_all_valid_users(response)
                new_users = self.get_new_users(all_valid_user)
                filtered_users.extend(new_users)

        yield filtered_users

    def get_new_users(self, all_users):
        new_users = []

        for user in all_users:
            if not self.cache.get_user_by_id(user['id']):
                new_users.append(user)

        return new_users


# group_name = requests.get('https://api.vk.com/method/groups.getById', params={
#                 'access_token': '',
#                 'v': 5.103,
#                 'group_id': '',
#                 'fields': 'name',
#             }).json()['response'][0]['name']


