"""
Скрипт сохраняющий в кэш всех подписчиков из групп.
Сравнивая кэш и состояние групп ВК будет происходить поиск новых подписчиков.
"""

import argparse

from accounts.manager import AccountManager
from db.redis_db import RedisAccess
from utils.logger import logger
from utils.utils import get_config, split_accounts_in_objects_and_authorize, \
    update_account_config, save_dump_date_in_config


parser = argparse.ArgumentParser()
parser.add_argument(
    "-b",
    '--rebuild',
    required=False,
    action='store_true',
    help="Drop and update current cache"
)
args = parser.parse_args()
cache = RedisAccess()

if args.rebuild:
    cache.drop_all()

if __name__ == "__main__":
    accounts, settings = map(get_config, ['accounts.json', 'config.json'])

    searcher_objects = split_accounts_in_objects_and_authorize(accounts, 'searchers')
    update_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        messages_examples={},
        delay_between_request=settings['second_delay_between_request'],
        groups=settings['groups'],
        manager_url=settings['manager_url'],

        is_caching=True,
    )
    manager.search_worker()
    save_dump_date_in_config(settings)
    users_count = cache.count_cache_users()
    logger.info(f"Зафиксировано состояние групп (`{settings['last_cache_dump_date']}`), "
                f"по которому будет происходить поиск новых подписчиков: \n"
                f"`{users_count}` пользователей из групп `{', '.join(settings['groups'])}` добавлено в кэш.")

