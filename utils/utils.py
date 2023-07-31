import json
import logging
from accounts.accounts import Account


def get_config(path: str) -> dict:
    with open(path, 'r') as config:
        return json.load(config)


def save_token_and_block_status_in_account_config(new_config) -> None:
    with open('accounts.json', 'w') as config:
        config.write(
            json.dumps(new_config, indent=2)
        )


def split_accounts_in_objects_and_authorize(account_config: dict, account_type: str) -> list:
    account_objects_list = []

    for account in account_config[account_type]:
        account_object = Account(**account)

        if not account_object.is_authenticated:
            account_object.set_access_token_from_vk()

        if account_object.is_blocked is True:
            account['is_blocked'] = True
            logging.warning(f"Аккаунт `{account_object.login}` заблокирован")
            continue

        if account_object.access_token is not None and not account['access_token']:
            account['access_token'] = account_object.access_token

        account_objects_list.append(account_object)

    return account_objects_list


def get_monitoring_date(date):
    new_date = date
    return new_date


def get_all_valid_users(users: dict) -> list:
    filtered_users = []

    for user in users['items']:
        # 1672531201 = Январь 01 2023
        if user.get('last_seen') is None or user.get('can_write_private_message') is None:
            continue

        if user['last_seen']['time'] >= 1672531201 and user['can_write_private_message'] == 1:
            filtered_users.append(user)

    return filtered_users

