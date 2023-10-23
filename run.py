from time import sleep

from accounts.accounts import AccountBuilder
from accounts.manager import AccountManager
from config.config import get_config
from db.mongo import MongoConnector
from utils.logger import logger


DB = MongoConnector.get_instance()
SETTING = get_config()


def _main():
    searchers, writers = DB.account_connector.get_searchers(), DB.account_connector.get_writers()
    builder = AccountBuilder(searchers_account=searchers, writers_account=writers)
    builder.build_accounts()
    searchers_accounts, writers_accounts = builder.get_build_searchers(), builder.get_build_writers()

    manager = AccountManager(
        search_accounts=searchers_accounts,
        write_accounts=writers_accounts,
        settings=SETTING
    )

    manager.search_worker()
    manager.write_worker()
    DB.account_connector.remove_blocked_accounts()
    logger.info("Цикл программы завершен")


if __name__ == "__main__":
    while True:
        _main()
        # Задержка между циклами search/write
        sleep(SETTING.get('minutes_delay_between_program_cycle') * 60)

# 4) Сделать cli для добавления группы к мониторингу,
# 4++) обнуление отправленных сообщений - раз в сутки
# 5++) Добавить schedule к скрипту
# 6) Распаралелить работу скрипта для воркеров и сечеров
# 6++) Рефакторинг
# 10) Затестить проект на боевых данных

