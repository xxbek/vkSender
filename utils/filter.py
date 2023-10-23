import json
import time
from datetime import datetime

from accounts.accounts import Account


def get_all_valid_users(users: dict, last_online_unix_time_filter: int, birth_date_filter=2005) -> list:
    """Функция, фильтрующая список пользователей по заданным критериям"""
    filtered_users = []

    # Если нужно задать дату последнего посещения вручную
    # user_filter_time = datetime(year=2023, month=8, day=10)
    # last_online_unix_time_filter = time.mktime(user_filter_time.timetuple())

    user_birthday_mask = '%d.%m.%Y'

    for user in users['items']:
        # Фильтрация на дату последнего посещения ВК
        if user.get('last_seen') is not None and user['last_seen']['time'] <= last_online_unix_time_filter:
            continue

        # Фильтрация на возвраст
        if user.get('bdate') is not None and len(user['bdate']) > 5:
            birth_day = user['bdate']
            user_birth_year = datetime.strptime(birth_day, user_birthday_mask).year
            if user_birth_year > birth_date_filter:
                continue

        # Фильтрация на возможность написать личное сообщение
        if user.get('can_write_private_message') is not None and user['can_write_private_message'] == 0:
            continue

        filtered_users.append(user)

    return filtered_users




