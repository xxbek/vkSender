import json


def get_config(path='./config/config.json') -> dict:
    with open(path, 'r') as config:
        return json.load(config)
