import logging
import random

from accounts.accounts import Account
from db.db import DBAccess
from db.redis_db import RedisAccess
from utils.utils import update_account_config, update_account_config_with_sent_messages_amount
from vk_request.vk_request import VKWriter, VKSearcher


class AccountManager:
    def __init__(
            self,
            delay_between_request: str,
            groups: list[str],
            messages_examples: dict,
            search_accounts: list[Account] = None,
            write_accounts: list[Account] = None,
            caching=False,
            message_limit=10,
    ):
        self._db = DBAccess
        self._cache = RedisAccess()
        self.delay = delay_between_request
        self._groups = groups
        self._search_accounts = search_accounts or []
        self._write_accounts = write_accounts or []
        self._searcher = VKSearcher
        self._writer = VKWriter
        self.caching = caching
        self.message_limit = message_limit
        self.messages_examples = messages_examples

    def search_worker(self):
        db = self._db()
        account = random.choice(self._search_accounts)
        searcher = self._searcher(db, RedisAccess(), account, self._groups, delay=self.delay, caching=self.caching)
        for vk_users in searcher.yield_users_from_groups():
            users = db.create_model_from_dict(vk_users)

            if self.caching is True:
                self._cache.save_users(users)
            else:
                db.add_users(users)
                self._cache.save_users(users)

    def write_worker(self):
        db = self._db()
        users = db.get_all_unwritten_users()
        possible_messages_to_send_now, messages_need_to_send = None, len(users)
        while possible_messages_to_send_now != 0 and messages_need_to_send != 0:
            messages_need_to_send = len(users)
            accounts_number = len(self._write_accounts)
            messages_was_already_sent = sum([account.messages_written for account in self._write_accounts])
            total_possible_sending_number = accounts_number * self.message_limit

            possible_messages_to_send_now = total_possible_sending_number - messages_was_already_sent

            if possible_messages_to_send_now < messages_need_to_send:
                logging.error(f'Число новых пользователей ({messages_need_to_send}) '
                                f'превышает пропускную способность аккаунтов '
                                f'({possible_messages_to_send_now} сообщений возможно отправить сейчас)')
                return
            message = random.choice(self.messages_examples['first_messages'])
            account = self._get_random_valid_account()
            writer = self._writer(db, self._cache, account, delay=self.delay)
            user = users.pop()
            writer.write_to_the_user(user, message, is_it_first_message=True)
            messages_need_to_send = len(users)

        for account in self._write_accounts:
            writer = self._writer(db, self._cache, account, delay=self.delay)
            writer.reply_to_unwritten_messages(self.messages_examples['second_messages'])

        update_account_config_with_sent_messages_amount(self._write_accounts)


    def _get_random_valid_account(self) -> Account:
        valid_accounts = [account for account in self._write_accounts if account.messages_written < self.message_limit]
        if len(valid_accounts):
            logging.error(f"Все аккаунты превысили лимит сообщений на сегодня")

        valid_account = random.choice(valid_accounts)

        return valid_account
