import logging
import sqlalchemy
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from db.models import User

DB_FILENAME = "db.sqlite"

engine = sqlalchemy.create_engine(f"sqlite:///{DB_FILENAME}", echo=True)
make_sqlite_session = sessionmaker(engine)


def get_db_session() -> Session:
    """return new database session"""
    try:
        new_session: Session = make_sqlite_session()
    except SQLAlchemyError as err:
        logging.error(f"Cannot connect to database: {err}")

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
            logging.info(f"Пользователь `{vk_id}: {first_name} {last_name}` добавлен в базу")

    def is_user_in_db(self, vk_id: str) -> bool:
        with self._session as session:
            user = session.query(User).filter(User.vk_id == vk_id)

        return True if user.count() == 1 else False

    def get_user_by_vk_id(self, vk_id: str) -> type(User) | None:
        with self._session as session:
            user = session.query(User).filter(User.vk_id == vk_id).all()

        if len(user) != 1:
            logging.error(
                f"Ошибка в базе данных: пользователь с идентификатором `{vk_id}` не существует или дублируется"
            )
            return None

        return user[0]

    def get_all_users(self) -> list[type(User)]:
        with self._session as session:
            users = session.query(User).all()
        return users









