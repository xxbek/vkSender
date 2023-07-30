import logging
from typing import Generator

import requests

from accounts.accounts import Account
from db.db import DBAccess


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
    def __init__(self, db: DBAccess, account: Account, group_list: list[str]):
        super().__init__(db, account)
        self.group_list = group_list

    def get_group_offset(self, group_id):
        response = requests.get('https://api.vk.com/method/groups.getMembers', params={
            'access_token': self._account.access_token,
            'v': 5.103,
            'group_id': group_id,
            'sort': 'id_desc',
            'offset': 0,
            'fields': 'last_seen',
        }).json()

        if response.get('error'):
            err_message = response.get('error').get('error_msg')
            logging.error(f'Ошибка при поиске пользователей в группе `{group_id}`: {err_message}')
            return

        users = response['response']['count']

        return users // 1000

    def yield_new_users_from_groups(self) -> Generator:
        for group in self.group_list:
            for user in self.yield_new_users_from_one_group(group):
                yield user
            logging.info(f"Группа `{group}` была просканированна")

    def yield_new_users_from_one_group(self, group_id) -> Generator:
        response = {}
        offset = 0
        max_offset = self.get_group_offset(group_id)
        while offset < max_offset:
            response = requests.get('https://api.vk.com/method/groups.getMembers', params={
                'access_token': self._account.access_token,
                'v': 5.103,
                'group_id': group_id,
                'sort': 'time_asc',
                'offset': offset,
                'fields': ['last_seen', 'can_write_private_message']
            }).json()['response']
            offset += 1

            # Обработать данные из вк и вернуть в удобноваримом виде
            print(response)
            # for item in response['items']:
            #     try:
            #         if item['last_seen']['time'] >= 1605571200:
            #             good_id_list.append(item['id'])
            #     except Exception as E:
            #         continue

        yield response


