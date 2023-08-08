import vk_api
import os
import json

from requests import Session

from utils.logger import logger


class Account:
    def __init__(self, login: str, password: str, proxy: dict, access_token=None, messages_written=0, is_blocked=False):
        self.login = login
        self.password = password
        self.proxy = proxy
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

    def set_access_token_from_vk(self):
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

        try:
            account = vk_api.VkApi(
                self.login,
                self.password,
                # app_id = 6222115
                app_id=2685278,
                captcha_handler=captcha_handler,
                # session=session
            )
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


def captcha_handler(captcha):
    key = input("Введите код из капчи по ссылке {0}: ".format(captcha.get_url())).strip()

    return captcha.try_again(key)


def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция.
    """

    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device
