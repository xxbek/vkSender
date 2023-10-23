import time

import requests
from requests import Response, Session

from accounts.accounts import Account
from config.config import get_config
from db.mongo import MongoConnector
from db.redis_db import RedisAccess
from utils.logger import logger
from utils.filter import get_all_valid_users


config = get_config()


class VKRequest:
    def __init__(self, account: Account):
        _db = MongoConnector.get_instance()
        self._user_db = _db.user_connector
        self._info_db = _db.info_connector
        self.cache = RedisAccess.get_instance()
        self._account = account
        self.delay = config.get('seconds_delay_between_program_request')
        self.session = Session()

    def sleep(self):
        time.sleep(self.delay)

    def _request(self, endpoint, params=None) -> Response:
        default_params = {
            'access_token': self._account.access_token,
            'v': 5.103,
            'lang': 0
        }
        default_params.update(params)
        response = requests.get(
            f'https://api.vk.com/method/{endpoint}',
            params=default_params,
            proxies=self._account.proxy
        )
        self.sleep()
        return response


class VKWriter(VKRequest):
    def __init__(self, account: Account):
        super().__init__(account)

    def write_to_the_user(self, user: dict, message: str, is_it_first_message=True):
        response = self._request(
            endpoint='messages.send',
            params={
                'user_id': user.get('vk_id'),
                'random_id': 1 if is_it_first_message else 2,
                'message': message,
                'dont_parse_links': 0
            }
        )
        error = response.json().get('error')
        if error:
            logger.error(
                f"Не удалось отправить сообщение пользователю {user.get('vk_id')} из аккаунта {self._account}: {error['error_msg']}"
            )
            if error.get('ban_info'):
                self._account.is_blocked = True
            return

        logger.info(f"Сообщение было отправлено пользователю {user.get('vk_id')} из аккаунта {self._account.login}")

        self._user_db.change_user_message_status(user.get('vk_id'))
        self._account.messages_written += 1 if is_it_first_message else 0

    def reply_to_unwritten_messages(self, second_messages: str):
        response = self._request(
            endpoint='messages.getConversations',
            params={'count': 200, 'filter': 'unread'}
        )

        error = response.json().get('error')
        if error:
            logger.error(
                f"Не удалось получить список непрочитанных сообщений у аккаунта {self._account.login}")
            return

        conversations = response.json()['response']['items']

        for conversation in conversations:
            user_id = conversation['last_message']['from_id']
            user = self._user_db.get_user_by_vk_id(user_id)
            if user:
                self.write_to_the_user(user, second_messages, is_it_first_message=False)


class VKSearcher(VKRequest):
    def __init__(self, account: Account, caching=False):
        super().__init__(account)
        self.caching = caching

    def _get_group_offset(self, group_id):
        response = self._request(
            endpoint='groups.getMembers',
            params={
                'group_id': group_id,
                'sort': 'id_desc',
                'offset': 0
            }
        ).json()

        if response.get('error'):
            err_message = response.get('error').get('error_msg')
            logger.error(f'Ошибка при поиске пользователей в группе `{group_id}`: {err_message}')
            return

        users = response['response']['count']

        return users // 1000

    def return_new_users_info_from_group(self, group_id: str) -> (list[dict], str):
        """Функция возвращает список новых подписчиков группы и название группы"""
        group_name = self._get_group_name(group_id)
        if group_name:
            new_followers = self.get_new_followers_from_group(group_id)
            logger.info(f"Группа `{group_name}` была просканированна, найдено {len(new_followers)} новых подписчиков")
            return new_followers, group_name

    def return_dump_info_from_group(self, group_id: str) -> (list[dict], str):
        """Функция возвращает список всех подписчиков группы и название группы"""
        group_name = self._get_group_name(group_id)
        if group_name:
            users_id = self.return_all_users_from_one_group(group_id)
            dict_users = self._create_template_vk_dict(users_id, group_name)
            logger.info(f"Группа `{group_name}` была просканированна, найдено {len(dict_users)} человек")
            return dict_users, group_name

    def return_all_users_from_one_group(self, group_id) -> list[int]:
        all_users = []
        offset = 0
        max_offset = self._get_group_offset(group_id)
        while offset <= max_offset:
            response = self._request(
                endpoint='groups.getMembers',
                params={
                    'sort': 'id_desc',
                    'group_id': group_id,
                    'offset': offset * 1000,
                    'count': 1000,
                }
            ).json()
            offset += 1

            if response.get('error'):
                err_message = response.get('error').get('error_msg')
                logger.error(f'Ошибка при поиске пользователей в группе `{group_id}`: {err_message}')
                return []

            response = response.get('response')
            users_pool: list = response['items']
            all_users.extend(users_pool)

        return all_users

    def _create_template_vk_dict(self, users_id: list[int], group_name: str) -> list[dict]:
        users_dict = []
        for vk_id in users_id:
            user = {
                'id': vk_id,
                'first_name': "TEMPLATE FIRST NAME",
                'last_name': "TEMPLATE LAST NAME",
                'group_name': group_name,
            }
            users_dict.append(user)
        return users_dict

    def get_new_followers_from_group(self, group_id) -> list[dict]:
        filtered_users = []
        offset = 0
        max_offset = self._get_group_offset(group_id)
        while offset <= max_offset:
            response = self._request(
                endpoint='groups.getMembers',
                params={
                    'sort': 'id_desc',
                    'group_id': group_id,
                    'offset': offset * 1000,
                    'fields': 'last_seen, can_write_private_message, bdate',
                    'count': 1000,
                }
            ).json()['response']
            offset += 1

            valid_followers: list = get_all_valid_users(
                users=response,
                last_online_unix_time_filter=self._info_db.get_last_cache_dump_date_unix()
            )
            new_followers = self.get_unique_users_compared_cache(valid_followers, group_id)
            filtered_users.extend(new_followers)

        return filtered_users

    def get_unique_users_compared_cache(self, all_users: list[dict], group_url: str):
        """Функция, проверяющая, есть ли данный пользователь в кэше"""
        new_users = []

        for user in all_users:
            if not self.cache.get_user_by_id(user['id'], group_url=group_url):
                new_users.append(user)

        return new_users

    def _get_group_name(self, group_id) -> str | None:
        response = self._request(endpoint='groups.getById', params={
            'group_id': group_id,
            'fields': 'name',
        })

        error = response.json()
        if error.get('error_code'):
            logger.error(f"Не удалось получить название группы {group_id}: {error['error_msg']}")
            return
        response = response.json()['response']
        group_name = response[0].get('name')

        return group_name
