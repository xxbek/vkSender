from accounts.manager import AccountManager
from utils.utils import get_config, split_accounts_in_objects_and_authorize

if __name__ == "__main__":
    accounts, settings = map(get_config, ['accounts.json', 'config.json'])

    searcher_objects = split_accounts_in_objects_and_authorize(accounts, 'searchers')

    manager = AccountManager(
        search_accounts=searcher_objects,
        delay_between_request=settings['second_delay_between_request'],
        groups=settings['groups'],
        caching=True
    )
    manager.search_worker()


