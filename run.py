import time

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
        groups=settings['groups'],
        manager_url=settings['manager_url']
    )

    while True:
        # manager.search_worker()
        manager.write_worker()
        logger.info("Цикл логгера завершен")
        time.sleep(200)



# TODO # 2) Агрегатор для сообщений пользователям - распределить и зарандомить
# TODO # 3) Достать название групп и вставить их в БД
# 4++) Неправильно работает фильтр (пустил чела с закрытой личкой), неправильно работает поиск подписчиков (пустил челов которые были подписаны давно)
# 4) Сделать cli для добавления группы к мониторингу, для обнуления отправленных сообщений - раз в сутки
# 5) Добавить проксирование к запросам к вк
# 5++) Добавить schedule к скрипту
# 6) Распаралелить работу скрипта
# 6++) Рефакторинг
# TODO # 7) Добавить родителький класс для vkreq
# 8) Добавить модульное тестирование
# 9) Оформить проект к выводу в прод
# 10) Затестить проект на боевых данных
# 11) Перенести все в Монгу и производить поиск тогда, когда число подписчиков в группе изменилось

