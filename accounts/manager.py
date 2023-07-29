from accounts.accounts import Account
from db.db import DBAccess
from vk_request.vk_request import VKWriter, VKSearcher


class AccountManager:
    def __init__(self, search_accounts: list[Account], write_accounts: list[Account], delay):
        self._db = DBAccess
        self.delay = delay
        self._search_accounts = search_accounts
        self._write_accounts = write_accounts
        self._searcher = VKWriter
        self._writer = VKSearcher




