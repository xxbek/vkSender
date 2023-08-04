from accounts.manager import AccountManager
from utils.logger import logger
from utils.utils import get_config, split_accounts_in_objects_and_authorize, \
    update_account_config


if __name__ == "__main__":

    accounts, settings, messages = map(get_config, ['accounts.json', 'config.json', 'messages.json'])
    searcher_objects = split_accounts_in_objects_and_authorize(accounts, 'searchers')
    writer_accounts = split_accounts_in_objects_and_authorize(accounts, 'writers')
    update_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        write_accounts=writer_accounts,
        messages_examples=messages,
        delay_between_request=settings['second_delay_between_request'],
        groups=settings['groups']
    )

    manager.search_worker()



# TODO 1) Логгирование с выводом даты операции, логирование для уровней и типов операций: важная, неважная, ошибка
# 2) Агрегатор для сообщений пользователям - распределить и зарандомить
# 3) Достать название групп и вставить их в БД
# 4) Сделать cli для обнуления прогресса воркеров
# 5) Добавить проксирование к запросам к вк
# 5++) Добавить schedule к скрипту
# 6) Рефакторинг
# 7) Добавить родителький класс для vkreq
# 8) Добавить модульное тестирование
# 9) Оформить проект к выводу в прод
# 10) Затестить проект на боевых данных

