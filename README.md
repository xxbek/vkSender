# vkSender
Interface for interacting with the social network VK


- alembic.ini

add url in alembic.ini  `sqlalchemy.url = sqlite:///db.sqlite`

- env.py: 

target_metadata = None

исправить

from db.models import Base
target_metadata = Base.metadata

на

alembic revision --autogenerate -m "first migrations"

alembic upgrade heads


-- Отключить двухфакторную аутентификацию

