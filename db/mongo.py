from datetime import datetime

from pydantic import ValidationError

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import PyMongoError

from config.config import get_config
from db.model import UserModel, AccountModel
from utils.logger import logger

config: dict = get_config()

_USER_COLLECTION = 'users'
_WORK_INFO_COLLECTION = 'info'

_WRITERS_COLLECTION = 'writers'
_SEARCHER_COLLECTION = 'searchers'


class MongoConnector:
    __instance = None

    def _mongo_setting(self):
        self._get_user_collection().create_index('vk_id', unique=True)

    @staticmethod
    def get_instance() -> Database:
        if MongoConnector.__instance is None:
            MongoConnector()
        return MongoConnector.__instance

    def __init__(self):
        if MongoConnector.__instance is not None:
            raise Exception("This class is a singleton!")
        else:
            client = MongoClient(config.get('mongo_uri'))
            MongoConnector.__instance = client[config.get('db_name')]
            MongoConnector.__instance.user_connector = _UserConnector()
            MongoConnector.__instance.info_connector = _InfoConnector()
            MongoConnector.__instance.account_connector = _AccountConnector()
            self._mongo_setting()
            logger.info('Connected to MongoDB')

    def _get_collection(self, collection: str):
        return self.get_instance()[collection]

    def _get_user_collection(self):
        return self._get_collection(_USER_COLLECTION)

    def _get_info_collection(self):
        return self._get_collection(_WORK_INFO_COLLECTION)

    def _get_writers_collection(self):
        return self._get_collection(_WRITERS_COLLECTION)

    def _get_searchers_collection(self):
        return self._get_collection(_SEARCHER_COLLECTION)


class _UserConnector(MongoConnector):
    def __init__(self):
        pass

    def add_user(self, user: UserModel):
        if self._is_user_in_db(user.vk_id):
            logger.info(f'Юзер {user.vk_id} уже записан в базу')
        insert_data = user.model_dump()
        user_collection = self._get_user_collection()
        user_collection.insert_one({**insert_data})
        logger.info(f"Новый подписчик `{user.vk_id}: "
                    f"{user.first_name} {user.last_name}` группы `{user.group_name}` добавлен в базу")

    def _is_user_in_db(self, vk_id: int) -> bool:
        user_collection = self._get_user_collection()
        user_number = user_collection.count_documents({'vk_id': vk_id})

        return True if user_number == 1 else False

    def add_users(self, users: list[UserModel]):
        for user in users:
            try:
                if self._is_user_in_db(vk_id=user.vk_id):
                    continue
                self.add_user(user)
            except PyMongoError as err:
                logger.error(f'Ошибка при добавлении нового пользователя {user} в базу данных: {err}')

    def get_user_by_vk_id(self, vk_id: str) -> UserModel | None:
        user_collection = self._get_user_collection()
        user = user_collection.count_documents({'vk_id': vk_id})

        if user > 1:
            logger.error(f"Пользователь с идентификатором `{vk_id}` дублируется")
            return None

        if user == 0:
            logger.error(f"Пользователь с идентификатором `{vk_id}` не существует в базе данных")

        return user_collection.find_one({'vk_id': vk_id})

    def get_all_unwritten_users(self) -> list[UserModel]:
        users_cursor = self._get_user_collection().find({'is_received_message': False})
        users_list = list(users_cursor)
        return users_list

    @staticmethod
    def create_model_from_dict(vk_users: list[dict], group_url, group_name) -> list[UserModel]:
        users = []
        for user in vk_users:
            try:
                user_model = UserModel(
                    group_url=group_url,
                    vk_id=user.get('id'),
                    first_name=user.get('first_name'),
                    last_name=user.get('last_name'),
                    group_name=group_name
                )
                users.append(user_model)
            except ValidationError as e:
                logger.error(f"Ошибка валидации пользователя: {e}")
            continue

        return users

    def change_user_message_status(self, vk_id: str):
        self._get_user_collection().find_one_and_update(
            {'vk_id': vk_id}, {
                "$set": {
                    'is_received_message': True
                }
            }
        )


class _InfoConnector(MongoConnector):
    def __init__(self):
        pass

    def save_last_dump_date(self):
        last_cache_dump_date = datetime.now()
        info_collection = self._get_info_collection()
        info_collection.insert_one({'date': last_cache_dump_date})

    def get_last_cache_dump_date_unix(self) -> int:
        info_collection = self._get_info_collection()
        last_date = info_collection.find_one(sort=[("date", -1)])
        date = last_date.get('date')

        return int(datetime.timestamp(date))

    def get_last_cache_dump_date_readable(self) -> str:
        info_collection = self._get_info_collection()
        last_date = info_collection.find_one(sort=[("date", -1)])
        date = last_date.get('date')

        return date


class _AccountConnector(MongoConnector):
    def __init__(self):
        pass

    ACCOUNTS_TYPE = (_WRITERS_COLLECTION, _SEARCHER_COLLECTION)

    def _get_account_collections(self):
        return [self._get_searchers_collection(), self._get_writers_collection()]

    def insert_account(self, account: AccountModel, account_type: str):
        account_dump = account.model_dump()
        if account_type == self.ACCOUNTS_TYPE[0]:
            writers = self._get_writers_collection()
            writers.insert_one(account_dump)
        else:
            searchers = self._get_searchers_collection()
            searchers.insert_one(account_dump)

    def get_writers(self) -> list[AccountModel]:
        writers = self._get_writers_collection().find({}, {"_id": False})

        return list(writers)

    def get_searchers(self) -> list[AccountModel]:
        searchers = self._get_searchers_collection().find({}, {"_id": False})

        return list(searchers)

    def save_access_token(self, login, token: str):
        for collection in self._get_account_collections():
            collection.find_one_and_update({'login': login}, {'$set': {'access_token': token}})

    def remove_blocked_accounts(self):
        for collection in self._get_account_collections():
            blocked_accounts = collection.find({'is_blocked': True})
            for account in list(blocked_accounts):
                logger.error(f'Аккаунт `login: {account.get("login")}` был заблокирован и удален из базы')
            result = collection.delete_many({'is_blocked': True})
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.error(f'Удалено {deleted_count} аккаунтов')


    def update_db_with_sent_messages_amount(self, accounts: list[AccountModel]):
        writer_collections = self._get_writers_collection()
        for account in accounts:
            writer_collections.find_one_and_update(
                {'login': account.login},
                {'$set': {'messages_written': account.messages_written}}
            )

