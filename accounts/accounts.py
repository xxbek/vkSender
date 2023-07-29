import vk_api
import os
import json


class Account:
    def __init__(self, login: str, password: str, proxy: dict, access_token=None, is_blocked=False):
        self.login = login
        self.password = password
        self.proxy = proxy
        self.access_token = access_token

        self.is_authenticated = True if self.access_token else False
        self.is_blocked = is_blocked

        if self.access_token is None:
            self.access_token = self._get_access_token_from_vk()

    def _get_access_token_from_vk(self):
        """
        Получение токена через логин и пароль.
        У пользователя должна отсутствовать двухфактораня аутентификация, иначе требуется
        дополнительный коллбек в VkApi для обработки звонка на телефон, привязанный к аккаунту
        """
        account = vk_api.VkApi(self.login, self.password, app_id=2685278)
        account.auth()
        account_api = account.get_api()
        access_token = None

        try:
            user = account_api.users.get()
        except Exception as err:
            print(f"Error: {err}")
        else:
            with open('vk_config.v2.json', 'r') as data_file:
                data = json.load(data_file)

            for xxx in data[self.login]['token'].keys():
                for yyy in data[self.login]['token'][xxx].keys():
                    access_token = data[self.login]['token'][xxx][yyy]['access_token']
            os.remove('vk_config.v2.json')

            return access_token


