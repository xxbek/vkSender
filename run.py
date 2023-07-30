import json
import logging

from accounts.accounts import Account
from accounts.manager import AccountManager


def _get_config(path: str) -> dict:
    with open(path, 'r') as config:
        return json.load(config)


def save_token_and_block_status_in_account_config(new_config) -> None:
    with open('accounts.json', 'w') as config:
        config.write(
            json.dumps(new_config, indent=2)
        )


def split_accounts_in_objects(account_config: dict, account_type: str) -> list:
    account_objects_list = []

    for account in account_config[account_type]:
        account_object = Account(**account)

        if account_object.is_blocked is True:
            account['is_blocked'] = True
            # logging.warning(f"Аккаунт `{account_object.login}` заблокирован")
            continue

        if account_object.access_token is not None and account['access_token'] is None:
            account['access_token'] = account_object.access_token

        account_objects_list.append(account_object)

    return account_objects_list

def get_monitoring_date(date):
    new_date = date

    return new_date


if __name__ == "__main__":

    accounts, settings, messages = map(_get_config, ['accounts.json', 'config.json', 'messages.json'])
    monitoring_start_date = get_monitoring_date(settings['monitoring_start_date'])

    searcher_objects = split_accounts_in_objects(accounts, 'searchers')
    writer_accounts = split_accounts_in_objects(accounts, 'writers')
    save_token_and_block_status_in_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        write_accounts=writer_accounts,
        delay=settings['second_delay_between_request'],
        monitoring_start_date=monitoring_start_date,
        groups=settings['groups']
    )

    print(manager.search_worker())



