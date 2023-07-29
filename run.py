import json

from accounts.accounts import Account
from accounts.manager import AccountManager


def _get_config(path: str) -> dict:
    with open(path, 'r') as config:
        return json.load(config)


def _update_accounts_config_property_by_login(login: str, property_name: str, property_value) -> None:
    accounts_cf = _get_config('accounts.json')
    for account in accounts_cf['searchers'] + accounts_cf['writers']:
        if account['login'] == login:
            account[property_name] = property_value

    with open('accounts.json', 'w') as config:
        config.write(
            json.dumps(accounts_cf, indent=2)
        )


def get_accounts_in_objects(account_config: dict) -> list:
    account_objects_list = []

    for account in account_config:
        account_object = Account(**account)

        if account_object.is_blocked is True:
            _update_accounts_config_property_by_login(account_object.login, 'is_blocked', True)
            continue

        if account_object.access_token is None and account.access_token is not None:
            _update_accounts_config_property_by_login(account_object.login, 'access_token', account_object.access_token)

        account_objects_list.append(account_object)

    return account_objects_list


if __name__ == "__main__":

    accounts, settings, messages = map(_get_config, ['accounts.json', 'config.json', 'messages.json'])

    searcher_accounts, writer_accounts = accounts['searchers'], accounts['writers']

    searcher_objects, writer_accounts = map(get_accounts_in_objects, [searcher_accounts, writer_accounts])

    manager = AccountManager(search_accounts=searcher_objects, write_accounts=writer_accounts, delay=settings['delay'])
    print(writer_accounts)



