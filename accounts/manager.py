import random

from accounts.accounts import Account
from config.config import get_config
from db.model import UserModel
from db.mongo import MongoConnector
from db.redis_db import RedisAccess
from utils.logger import logger
from vk_request.vk_request import VKWriter, VKSearcher

from multiprocessing.dummy import Pool as ThreadPool

MESSAGES_CONFIG = get_config('messages.json')


class AccountManager:
    def __init__(
            self,
            settings: dict,
            search_accounts: list[Account] = None,
            write_accounts: list[Account] = None
    ):
        self._user_db = MongoConnector.get_instance().user_connector
        self._account_db = MongoConnector.get_instance().account_connector
        self._cache = RedisAccess.get_instance()
        self._search_accounts = search_accounts or []
        self._write_accounts = write_accounts or []
        self._searcher = VKSearcher
        self._writer = VKWriter

        self._delay: int = settings['minutes_delay_between_program_cycle']
        self._groups: list[str] = settings['groups']

        self.message_limit = settings['message_limit_per_one_account']

        self.messages_config: dict = MESSAGES_CONFIG

    def search_worker(self):
        pool = ThreadPool(2)
        pool.map(self.save_new_followers_from_group, self._groups)
        pool.close()
        pool.join()

    def save_new_followers_from_group(self, group_id):
        account = random.choice(self._search_accounts)
        searcher = self._searcher(account)
        new_followers, group_name = searcher.return_new_users_info_from_group(group_id)
        users = self._user_db.create_model_from_dict(vk_users=new_followers, group_url=group_id, group_name=group_name)
        self._user_db.add_users(users)
        self._cache.save_users(users)

    def write_worker(self):
        users = self._user_db.get_all_unwritten_users()
        possible_messages_to_send_now, messages_need_to_send = None, len(users)
        while possible_messages_to_send_now != 0 and messages_need_to_send != 0:
            messages_need_to_send = len(users)
            accounts_number = len(self._write_accounts)
            messages_was_already_sent = sum([account.messages_written for account in self._write_accounts])
            total_possible_sending_number = accounts_number * self.message_limit

            possible_messages_to_send_now = total_possible_sending_number - messages_was_already_sent

            if possible_messages_to_send_now < messages_need_to_send:
                logger.error(f'Число новых пользователей ({messages_need_to_send}) '
                                f'превышает пропускную способность аккаунтов '
                                f'({possible_messages_to_send_now} сообщений возможно отправить сейчас)')
                return

            account = self._get_random_valid_account()
            writer = self._writer(account)
            user = users.pop()
            message = self._create_first_message(user)
            writer.write_to_the_user(user, message, is_it_first_message=True)
            messages_need_to_send = len(users)

        self.reply_to_all_unwritten_messages()

        self._account_db.update_db_with_sent_messages_amount(self._write_accounts)

    def dump_users_from_groups_in_cache(self):
        pool = ThreadPool(2)
        result = pool.map(self.dump_users_from_one_group, self._groups)
        pool.close()
        pool.join()
        return sum(result)

    def dump_users_from_one_group(self, group_id: str) -> int:
        account = random.choice(self._search_accounts)
        searcher = self._searcher(account, caching=True)
        vk_users, group_name = searcher.return_dump_info_from_group(group_id)
        users = self._user_db.create_model_from_dict(vk_users=vk_users, group_url=group_id, group_name=group_name)
        new_users = self._cache.save_users(users)
        return new_users

    def reply_to_all_unwritten_messages(self):
        for account in self._write_accounts:
            writer = self._writer(account)
            message_template = random.choice(self.messages_config['second_messages'])
            reply_message = message_template.format(manager=self.messages_config['manager_url'])
            writer.reply_to_unwritten_messages(reply_message)

    def _get_random_valid_account(self) -> Account:
        valid_accounts = [account for account in self._write_accounts if account.messages_written < self.message_limit]
        if len(valid_accounts) == 0:
            logger.error(f"Все аккаунты превысили лимит сообщений на сегодня")

        valid_account = random.choice(valid_accounts)

        return valid_account

    def _create_first_message(self, user: UserModel) -> str:
        message_template = random.choice(self.messages_config['first_messages'])
        message = message_template.format(
            user=user.get('first_name'),
            group_name=user.get('group_name'),
            manager=self.messages_config['manager_url']
        )
        return message

