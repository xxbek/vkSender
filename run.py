from time import sleep

import db.db
from accounts.manager import AccountManager
from utils.logger import logger
from utils.utils import get_config, split_accounts_in_objects_and_authorize, \
    update_account_config

def _main():
    accounts, settings, messages = map(get_config, ['accounts.json', 'config.json', 'messages.json'])
    searcher_objects = split_accounts_in_objects_and_authorize(accounts, 'searchers')
    writer_accounts = split_accounts_in_objects_and_authorize(accounts, 'writers')
    update_account_config(accounts)

    manager = AccountManager(
        search_accounts=searcher_objects,
        write_accounts=writer_accounts,
        messages_examples=messages,
        settings=settings
    )

    manager.search_worker()
    # manager.write_worker()
    logger.info("Цикл воркеров завершен")


if __name__ == "__main__":
    while True:
        _main()
        sleep(10)



# 4) Сделать cli для добавления группы к мониторингу, для обнуления отправленных сообщений - раз в сутки
# 5) Добавить проксирование к запросам к вк
# 5++) Добавить schedule к скрипту
# 6) Распаралелить работу скрипта
# 6++) Рефакторинг
# 8) Добавить модульное тестирование
# 9) Оформить проект к выводу в прод
# 10) Затестить проект на боевых данных
# 11) Перенести все в Монгу и производить поиск тогда, когда число подписчиков в группе изменилось


# 12) Сделать отдельный класс/метод для кеширования одной группы, где будут сохраняться абсолютно все аккаунты

