import logging

from accounts.manager import AccountManager
from utils.utils import get_config, split_accounts_in_objects_and_authorize, \
    save_token_and_block_status_in_account_config

logging.basicConfig(format='%(process)d-%(levelname)s-%(message)s', level=logging.DEBUG)

if __name__ == "__main__":

    accounts, settings, messages = map(get_config, ['accounts.json', 'config.json', 'messages.json'])

    searcher_objects = split_accounts_in_objects_and_authorize(accounts, 'searchers')
    writer_accounts = split_accounts_in_objects_and_authorize(accounts, 'writers')
    save_token_and_block_status_in_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        write_accounts=writer_accounts,
        delay_between_request=settings['second_delay_between_request'],
        groups=settings['groups']
    )

    manager.write_worker()



