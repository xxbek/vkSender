import sqlalchemy
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from db.models import User
from utils.logger import logger

DB_FILENAME = "db.sqlite"

engine = sqlalchemy.create_engine(f"sqlite:///{DB_FILENAME}")
make_sqlite_session = sessionmaker(engine)


def get_db_session() -> Session:
    """return new database session"""
    try:
        new_session: Session = make_sqlite_session()
    except SQLAlchemyError as err:
        logger.error(f"Cannot connect to database: {err}")

    return new_session


class DBAccess:
    """Data Access Layer for operating user info"""
    def __init__(self):
        self._session = get_db_session()

    def add_user(self, vk_id, first_name, last_name, group_url, group_name) -> None:
        with self._session as session:
            user = User(
                vk_id=vk_id,
                first_name=first_name,
                last_name=last_name,
                group_url=group_url,
                group_name=group_name
            )
            session.add(user)
            session.commit()
            logger.info(f"Новый подписчик `{vk_id}: {first_name} {last_name}` группы {group_name} добавлен в базу")

    def add_users(self, users: list[User]):
        for user in users:
            try:
                self.add_user(user.vk_id, user.first_name, user.last_name, user.group_url, user.group_name)
            except sqlalchemy.exc.SQLAlchemyError as err:
                logger.error(f'Ошибка при добавлении нового пользователя {User} в базу данных: {err}')

    def is_user_in_db(self, vk_id: str) -> bool:
        with self._session as session:
            user = session.query(User).filter(User.vk_id == vk_id)

        return True if user.count() == 1 else False

    def get_user_by_vk_id(self, vk_id: str) -> type(User) | None:
        with self._session as session:
            user = session.query(User).filter(User.vk_id == vk_id).all()

        if len(user) != 1:
            logger.error(
                f"Ошибка в базе данных: пользователь с идентификатором `{vk_id}` не существует или дублируется"
            )
            return None

        return user[0]

    def get_all_unwritten_users(self) -> list[type(User)]:
        with self._session as session:
            users = session.query(User).filter(User.is_received_message == 0).all()
        return users

    def create_model_from_dict(self, vk_users: dict) -> list[User]:
        users = []
        for user in vk_users:
            user_model = User(
                vk_id=user['id'],
                first_name=user['first_name'],
                last_name=user['last_name'],
                group_url='template',
                group_name='template'
            )
            users.append(user_model)

        return users

    def change_user_message_status(self, vk_id: str):
        with self._session as session:
            user = session.query(User).filter(User.vk_id == int(vk_id)).one()
            user.is_received_message = 1
            session.commit()
            
        return user

    def drop_users(self):
        with self._session as session:
            session.execute(text("TRUNCATE TABLE users"))










