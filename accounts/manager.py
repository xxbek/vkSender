from accounts.accounts import Account
from db.db import DBAccess
from db.redis_db import RedisAccess
from vk_request.vk_request import VKWriter, VKSearcher


class AccountManager:
    def __init__(
            self,
            delay_between_request: str,
            groups: list[str],
            search_accounts: list[Account] = None,
            write_accounts: list[Account] = None,
            caching=False,
    ):
        self._db = DBAccess
        self._cache = RedisAccess()
        self.delay_between_request = delay_between_request
        self._groups = groups
        self._search_accounts = search_accounts or []
        self._write_accounts = write_accounts or []
        self._searcher = VKSearcher
        self._writer = VKWriter
        self.caching = caching

    def search_worker(self):
        db = self._db()
        for account in self._search_accounts:
            searcher = self._searcher(db, account, self._groups, caching=self.caching)
            for vk_users in searcher.yield_users_from_groups():
                users = db.create_model_from_dict(vk_users)

                if self.caching is True:
                    self._cache.save_users(users)
                else:
                    db.add_users(users)

    def write_worker(self):
        pass

