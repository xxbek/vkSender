import json
import time
from datetime import datetime

from accounts.accounts import Account


def get_config(path: str) -> dict:
    with open(path, 'r') as config:
        return json.load(config)


def update_account_config_with_sent_messages_amount(accounts: list[Account]):
    config = get_config('accounts.json')
    config_writers: list = config["writers"]

    for account in accounts:
        for config_account in config_writers:
            if account.login == config_account['login']:
                config_account['messages_written'] = account.messages_written
                continue
    config["writers"] = config_writers
    update_account_config(config)


def update_account_config(new_config) -> None:
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
            continue

        if account_object.access_token is not None:
            account['access_token'] = account_object.access_token

        account['is_blocked'] = account_object.is_blocked
        account_objects_list.append(account_object)

    return account_objects_list


def from_unix_timestamp_to_date(unix_time: int):
    readable_date = datetime.utcfromtimestamp(unix_time).strftime('%Y-%m-%d %H:%M:%S')
    return readable_date


def from_date_to_unix_timestamp(date: str):
    formated_date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    unix_timestamp = datetime.timestamp(formated_date)
    return unix_timestamp


def get_all_valid_users(users: dict) -> list:
    """Функция, фильтрующая список пользователей по заданным критериям"""
    filtered_users = []

    user_filter_time = datetime(year=2023, month=8, day=10)
    unixtime = time.mktime(user_filter_time.timetuple())

    user_birthday_mask = '%d.%m.%Y'

    for user in users['items']:
        # Фильтрация на дату последнего посещения ВК
        if user.get('last_seen') is not None and user['last_seen']['time'] <= unixtime:
            continue

        # Фильтрация на возвраст
        if user.get('bdate') is not None and len(user['bdate']) > 5:
            birth_day = user['bdate']
            user_birth_year = datetime.strptime(birth_day, user_birthday_mask).year
            if user_birth_year > 2005:
                continue

        # Фильтрация на возможность написать личное сообщение
        if user.get('can_write_private_message') is not None and user['can_write_private_message'] == 0:
            continue

        filtered_users.append(user)

    return filtered_users


def save_dump_date_in_config(new_setting: dict) -> None:
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_setting['last_cache_dump_date'] = current_date
    with open('config.json', 'w') as config:
        config.write(
            json.dumps(new_setting, indent=2)
        )



