"""
Скрипт сохраняющий в кэш всех подписчиков из групп.
Сравнивая кэш и состояние групп ВК будет происходить поиск новых подписчиков.
"""

import argparse

from accounts.accounts import AccountBuilder
from accounts.manager import AccountManager
from db.mongo import MongoConnector
from db.redis_db import RedisAccess
from utils.logger import logger
from config.config import get_config

parser = argparse.ArgumentParser()
parser.add_argument(
    "-b",
    '--rebuild',
    required=False,
    action='store_true',
    help="Drop and update current cache"
)
args = parser.parse_args()

DB = MongoConnector.get_instance()
SETTING = get_config()
CACHE = RedisAccess.get_instance()
if args.rebuild:
    CACHE.drop_all()

if __name__ == "__main__":
    settings = get_config()
    searchers = DB.account_connector.get_searchers()
    builder = AccountBuilder(searchers_account=searchers)
    builder.build_accounts()
    searchers_accounts = builder.get_build_searchers()

    manager = AccountManager(
        search_accounts=searchers_accounts,
        settings=settings
    )
    user_founded = manager.dump_users_from_groups_in_cache()
    DB.info_connector.save_last_dump_date()
    all_users_in_cache = CACHE.count_cache_users()
    logger.info(f"Зафиксировано состояние групп (`{DB.info_connector.get_last_cache_dump_date_readable()}`), "
                f"по которому будет происходить поиск новых подписчиков: \n"
                f"`{user_founded} новых (всего {all_users_in_cache})` пользователей из групп `{', '.join(settings['groups'])}` добавлено в кэш.")

