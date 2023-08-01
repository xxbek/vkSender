import logging
import argparse

from accounts.manager import AccountManager
from db.redis_db import RedisAccess
from utils.utils import get_config, split_accounts_in_objects_and_authorize, \
    save_token_and_block_status_in_account_config, save_dump_date_in_config

logging.basicConfig(format='%(process)d-%(levelname)s-%(message)s', level=logging.DEBUG)

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
    save_token_and_block_status_in_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        delay_between_request=settings['second_delay_between_request'],
        groups=settings['groups'],
        caching=True
    )
    manager.search_worker()
    save_dump_date_in_config(settings)
    users_count = cache.count_cache_users()
    logging.info(f"Произведена запись `{users_count}` пользователей из групп `{', '.join(settings['groups'])}` в кэш")

