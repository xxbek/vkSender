from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    vk_id = Column(Integer, unique=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    group_url = Column(String, nullable=False)
    group_name = Column(String, nullable=False)

