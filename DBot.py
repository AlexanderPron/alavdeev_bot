from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from bot_models import Users
from botObjects import UserData


class DBot(object):
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
