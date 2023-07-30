from accounts.accounts import Account
from db.db import DBAccess
from vk_request.vk_request import VKWriter, VKSearcher


class AccountManager:
    def __init__(
            self,
            search_accounts: list[Account],
            write_accounts: list[Account],
            delay: str,
            monitoring_start_date: str,
            groups: list[str]
    ):
        self._db = DBAccess
        self.delay = delay
        self._monitoring_start_date = monitoring_start_date
        self._groups = groups
        self._search_accounts = search_accounts
        self._write_accounts = write_accounts
        self._searcher = VKSearcher
        self._writer = VKWriter

    def search_worker(self):
        db = self._db()
        for account in self._search_accounts:
            searcher = self._searcher(db, account, self._groups)
            for new_vk_users in searcher.yield_new_users_from_groups():
                users_models = db.create_model_from_dict(new_vk_users)
                db.add_users(users_models)

    def write_worker(self):
        pass



