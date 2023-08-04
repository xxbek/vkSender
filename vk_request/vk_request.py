import time
from typing import Generator

import requests

from accounts.accounts import Account
from db.db import DBAccess
from db.models import User
from db.redis_db import RedisAccess
from utils.logger import logger
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

    def write_to_the_user(self, user: User, message: str, is_it_first_message=True):
        self.sleep()
        response = requests.get('https://api.vk.com/method/messages.send', params={
            'access_token': self._account.access_token,
            'v': 5.103,
            'user_id': user.vk_id,
            'random_id': 1 if is_it_first_message else 2,
            'message': message + ' https://vk.com/cutebeawer',
            'dont_parse_links': 0,
        })

        if response.status_code == 200:
            logger.info(f"Сообщение было отправлено пользователю {user.vk_id} из аккаунта {self._account.login}")

        self._db.change_user_message_status(user.vk_id)
        self._account.messages_written += 1

    def reply_to_unwritten_messages(self, second_messages: str):
        self.sleep()
        response = requests.get('https://api.vk.com/method/messages.getConversations', params={
            'access_token': self._account.access_token,
            'v': 5.103,
            'count': 200,
            'filter': 'unread',
        })

        conversations = response.json()['response']['items']

        if response.status_code != 200:
            logger.error(f"не удалось получить список непрочитанных сообщений у пользователя {self._account.login}")
            return

        for conversation in conversations:
            user_id = conversation['last_message']['from_id']
            user = self._db.get_user_by_vk_id(user_id)
            if user:
                # TODO Перенести message
                self.write_to_the_user(user, second_messages[0], is_it_first_message=False)


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
            logger.error(f'Ошибка при поиске пользователей в группе `{group_id}`: {err_message}')
            return

        users = response['response']['count']

        return users // 1000

    def yield_users_from_groups(self) -> Generator:
        for group in self.group_list:
            for new_user in self.yield_users_from_one_group(group):
                yield new_user
            logger.info(f"Группа `{group}` была просканированна, найдено {len(new_user)} человек")

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


