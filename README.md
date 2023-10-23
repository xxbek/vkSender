# vkSender
Interface for interacting with the social network VK

## Запуск кеша Redis и Mongo: 
> docker compose ud -d

(или локально установить)

- Перед запуском необходимо отключить двухфакторную аутентификацию для search/write аккаунтов

Запуск окружения и установка зависимостей:
> python -m venv venv 

> pip install -r requirement

> source venv/bin/activate

Сбор юзеров в кэш:
> python collect.py (-b для удаления предыдущего кэша)

Запуск search/write воркеров:
> python run.py
