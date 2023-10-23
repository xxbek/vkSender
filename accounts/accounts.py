import vk_api
import os
import json

from requests import Session

from utils.logger import logger

from db.mongo import MongoConnector


db = MongoConnector.get_instance()


class Account:
    def __init__(
            self,
            login: str,
            password: str,
            proxy_ip: str,
            proxy_port: str,
            proxy_login: str,
            proxy_pass: str,
            is_blocked: bool,
            access_token: str,
            messages_written: int = 0,
    ):
        self.login = login
        self.password = password
        self.proxy = {'http': f'socks5://{proxy_login}:{proxy_pass}@{proxy_ip}:{proxy_port}'}

        self.messages_written = messages_written
        self.access_token = self._check_access_token(access_token)
        self.is_authenticated = True if self.access_token else False
        self.is_blocked = is_blocked

    def __str__(self):
        return f"{self.login}"

    def __repr__(self):
        return f"{self.login}"

    def _check_access_token(self, access_token: str) -> str | None:
        if not access_token:
            return None
        try:
            vk_session = vk_api.VkApi(login=self.login, password=self.password, token=access_token)
            vk = vk_session.get_api()
            account_info = vk.account.getProfileInfo()
            user_info = vk.users.get(user_ids=account_info.get('id'), fields='deactivated')

        except vk_api.AuthError as err:
            logger.error(f"Ошибка при авторизации аккаунта  {self.login}: {err}")
            return None
        except vk_api.ApiError as err:
            logger.error(f"Ошибка при авторизации аккаунта {self.login}: {err}")
            return None

        return access_token

    def _get_vk(self):
        session = Session()
        session.proxies.update(self.proxy)
        return vk_api.VkApi(
            self.login,
            self.password,
            # app_id = 6222115
            app_id=2685278,
            captcha_handler=_captcha_handler,
            # session=session
        )

    def _set_access_token_from_vk(self):
        """
        Получение токена через логин и пароль.
        У пользователя должна отсутствовать двухфактораня аутентификация, иначе требуется
        дополнительный коллбек в VkApi для обработки звонка на телефон, привязанный к аккаунту
        """
        access_token = None

        # session = Session()
        # session.proxies = {'http': 'http://127.0.0.1:8000'}

        # pip install pysocks
        # session.proxies.update({'http': 'socks5://user:password@127.0.0.1:8000'})
        # session = Session()
        # session.proxies.update(
        #
        # )

        try:
            account = self._get_vk()
            account.auth()
            account_api = account.get_api()
        except vk_api.AuthError as error_msg:
            logger.error(f"Ошибка при авторизации аккаунта: {error_msg}")
            self.access_token = access_token
            return

        try:
            user = account_api.users.get()
        except vk_api.ApiError as err:
            logger.warning(f"Аккаунт {self.login} был заблокирован: {err}")
            self.is_blocked = True
        else:
            with open('vk_config.v2.json', 'r') as data_file:
                data = json.load(data_file)

            for xxx in data[self.login]['token'].keys():
                for yyy in data[self.login]['token'][xxx].keys():
                    access_token = data[self.login]['token'][xxx][yyy]['access_token']
            os.remove('vk_config.v2.json')
            self.is_blocked = False
            self.access_token = access_token


def _captcha_handler(captcha):
    key = input("Введите код из капчи по ссылке {0}: ".format(captcha.get_url())).strip()

    return captcha.try_again(key)


def _auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """

    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device


class AccountBuilder:
    def __init__(self, searchers_account: list[dict] = None, writers_account: list[dict] = None):
        self.searchers_account = [Account(**searcher) for searcher in searchers_account or []]
        self.writers_account = [Account(**writer) for writer in writers_account or []]

    def build_accounts(self) -> None:
        for account in self.searchers_account + self.writers_account:
            db.account_connector.save_access_token(account.login, 'temp_token')

            if not account.is_authenticated:
                account._set_access_token_from_vk()

            if account.is_blocked is True:
                logger.error(f'Аккаунт {account} был заблокирован')
                continue
            db.account_connector.save_access_token(account.login, account.access_token)

    def get_build_writers(self) -> list[Account]:
        if not self.writers_account:
            raise Exception('No writers provided!')
        return self.writers_account

    def get_build_searchers(self) -> list[Account]:
        if not self.searchers_account:
            raise Exception('No searchers provided!')
        return self.searchers_account
