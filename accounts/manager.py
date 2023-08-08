import random

from accounts.accounts import Account
from db.db import DBAccess
from db.models import User
from db.redis_db import RedisAccess
from utils.logger import logger
from utils.utils import update_account_config_with_sent_messages_amount
from vk_request.vk_request import VKWriter, VKSearcher


class AccountManager:
    def __init__(
            self,
            messages_examples: dict,
            settings: dict,
            search_accounts: list[Account] = None,
            write_accounts: list[Account] = None,
            is_caching=False,
    ):
        self._db = DBAccess
        self._cache = RedisAccess()
        self._search_accounts = search_accounts or []
        self._write_accounts = write_accounts or []
        self._searcher = VKSearcher
        self._writer = VKWriter

        self.messages_examples: dict = messages_examples

        self._delay: int = settings['second_delay_between_request']
        self._groups: list[str] = settings['groups']
        self._manager_url: str = settings['manager_url']
        self.message_limit = settings['message_limit_per_one_account']

        self.is_caching: bool = is_caching

    def search_worker(self):
        db = self._db()
        account = random.choice(self._search_accounts)
        searcher = self._searcher(db, RedisAccess(), account, delay=self._delay, caching=self.is_caching)
        for vk_users, group_name in searcher.yield_users_from_groups(self._groups):
            users = db.create_model_from_dict(vk_users, group_name)

            if self.is_caching is True:
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
                logger.error(f'Число новых пользователей ({messages_need_to_send}) '
                                f'превышает пропускную способность аккаунтов '
                                f'({possible_messages_to_send_now} сообщений возможно отправить сейчас)')
                return

            account = self._get_random_valid_account()
            writer = self._writer(db, self._cache, account, delay=self._delay)
            user = users.pop()
            message = self._create_first_message(user)
            writer.write_to_the_user(user, message, is_it_first_message=True)
            messages_need_to_send = len(users)

        self.reply_to_unwritten_messages(db)

        update_account_config_with_sent_messages_amount(self._write_accounts)

    def reply_to_unwritten_messages(self, db):
        for account in self._write_accounts:
            writer = self._writer(db, self._cache, account, delay=self._delay)
            reply_message = random.choice(self.messages_examples['second_messages']).format(manager=self._manager_url)
            writer.reply_to_unwritten_messages(reply_message)

    def _get_random_valid_account(self) -> Account:
        valid_accounts = [account for account in self._write_accounts if account.messages_written < self.message_limit]
        if len(valid_accounts) == 0:
            logger.error(f"Все аккаунты превысили лимит сообщений на сегодня")

        valid_account = random.choice(valid_accounts)

        return valid_account

    def _create_first_message(self, user: User) -> str:
        message_template = random.choice(self.messages_examples['first_messages'])
        message = message_template.format(
            user=user.first_name,
            group_name=user.group_name,
            manager=self._manager_url
        )
        return message

