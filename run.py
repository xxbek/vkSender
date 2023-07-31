from accounts.manager import AccountManager
from utils.utils import get_config, get_monitoring_date, split_accounts_in_objects_and_authorize, \
    save_token_and_block_status_in_account_config


if __name__ == "__main__":

    accounts, settings, messages = map(get_config, ['accounts.json', 'config.json', 'messages.json'])
    monitoring_start_date = get_monitoring_date(settings['monitoring_start_date'])

    searcher_objects = split_accounts_in_objects_and_authorize(accounts, 'searchers')
    writer_accounts = split_accounts_in_objects_and_authorize(accounts, 'writers')
    save_token_and_block_status_in_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        write_accounts=writer_accounts,
        delay_between_request=settings['second_delay_between_request'],
        monitoring_start_date=monitoring_start_date,
        groups=settings['groups']
    )

    print(manager.search_worker())



