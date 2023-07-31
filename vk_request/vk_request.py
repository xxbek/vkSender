import logging
import time
from typing import Generator

import requests

from accounts.accounts import Account
from db.db import DBAccess
from utils.utils import get_all_valid_users


class VKRequest:
    def __init__(self, db: DBAccess, account: Account):
        self._db = db
        self._account = account


class VKWriter(VKRequest):
    def get_users_from_db(self) -> list:
        pass

    def write_to_the_user(self, message: str):
        pass


class VKSearcher(VKRequest):
    def __init__(self, db: DBAccess, account: Account, group_list: list[str], caching=False):
        super().__init__(db, account)
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
            logging.info(f"Группа `{group}` была просканированна")

    def yield_users_from_one_group(self, group_id) -> Generator:
        filtered_users = []
        offset = 0
        max_offset = self.get_group_offset(group_id)
        while offset < max_offset:
            time.sleep(1)
            response = requests.get('https://api.vk.com/method/groups.getMembers', params={
                'access_token': self._account.access_token,
                'v': 5.103,
                'group_id': group_id,
                'sort': 'id_desc',
                'offset': 0,
                'fields': 'last_seen, can_write_private_message',
            }).json()['response']
            offset += 1

            if self.caching:
                all_valid_user: list = get_all_valid_users(response)
                filtered_users.extend(all_valid_user)
            else:
                new_users = self.get_new_users(response)
                filtered_users.extend(new_users)

        yield filtered_users

    def get_new_users(self, all_users):
        new_users = []
        return new_users


# group_name = requests.get('https://api.vk.com/method/groups.getById', params={
#                 'access_token': '',
#                 'v': 5.103,
#                 'group_id': '',
#                 'fields': 'name',
#             }).json()['response'][0]['name']


