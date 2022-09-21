from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from bot_models import Users
from botObjects import UserData
from sqlalchemy.exc import (
    MultipleResultsFound,
    NoResultFound,
)


def user_record_to_userdata(users_list: Users):
    """Функция перевода списка кортежей записей пользователей в список объектов UserData"""
    user_obj_list = []
    for user in users_list:
        return_user = UserData(
            id=user.id,
            name=user.name,
            lastname=user.lastname,
            tg_username=user.tg_username,
            tg_chat_id=user.tg_chat_id,
        )
        user_obj_list.append(return_user)
    return user_obj_list


class DBot(object):
    """Класс для работы с БД"""

    def __init__(self, engine_str):
        self.engine = create_engine(engine_str)
        self.session = Session(bind=self.engine)

    def add_user(self, user: UserData):
        new_user = Users(
            name=user.name,
            lastname=user.lastname,
            tg_username=user.tg_username,
            tg_chat_id=user.tg_chat_id,
        )
        self.session.add(new_user)
        self.session.commit()
        self.session.refresh(new_user)
        return new_user

    def get_user(self, tg_username=None, tg_chat_id=None):
        if tg_username:
            try:
                user = self.session.query(Users).filter(Users.tg_username == tg_username)
            except MultipleResultsFound:
                return False
            except NoResultFound:
                return False
        if tg_chat_id:
            try:
                user = self.session.query(Users).filter(Users.tg_chat_id == tg_chat_id)
            except MultipleResultsFound:
                return False
            except NoResultFound:
                return False
        return user_record_to_userdata(user)
