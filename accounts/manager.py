import logging
import random

from accounts.accounts import Account
from db.db import DBAccess
from db.redis_db import RedisAccess
from vk_request.vk_request import VKWriter, VKSearcher


class AccountManager:
    def __init__(
            self,
            delay_between_request: str,
            groups: list[str],
            search_accounts: list[Account] = None,
            write_accounts: list[Account] = None,
            caching=False,
            message_limit=10,
            messages_examples=None
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
        self.messages_examples = messages_examples or []

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
        possible_messages_to_send_now, messages_need_to_send = None, None
        users = db.get_all_unwritten_users()
        while possible_messages_to_send_now != 0 and messages_need_to_send != 0:
            messages_need_to_send = len(users)
            accounts_number = len(self._write_accounts)
            messages_was_already_sent = sum([message_sent for message_sent in self._write_accounts])
            total_possible_sending_number = accounts_number * self.message_limit

            possible_messages_to_send_now = total_possible_sending_number - messages_was_already_sent

            if possible_messages_to_send_now < messages_need_to_send:
                logging.error(f'Число новых пользователей ({messages_need_to_send}) '
                                f'превышает пропускную способность аккаунтов '
                                f'({possible_messages_to_send_now} сообщений возможно отправить сейчас)')
                return
            message = random.choice(self.messages_examples)
            account = self._get_random_valid_writer()
            writer = self._writer(db, self._cache, account)
            user = users.pop()
            writer.write_to_the_user(user, message)

    def _get_random_valid_writer(self) -> Account:
        account = random.choice(self._write_accounts)
        while account.messages_written >= self.message_limit:
            account = random.choice(self._write_accounts)

        return account
