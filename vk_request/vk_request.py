from accounts.accounts import Account
from db.db import DBAccess


class VKRequest:
    def __init__(self, db: DBAccess, account: Account):
        self._db = db
        self._account = account


class VKWriter(VKRequest):
    def get_users_from_db(self) -> list:
        pass

    def write_to_the_user(self, message: str):
        pass


class VKSearcher(VKRequest):
    def get_users_in_group(self, group_name: str):
        pass

    def save_user_in_db(self, user):
        pass

