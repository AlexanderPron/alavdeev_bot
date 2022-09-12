from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()
engine = create_engine('postgresql+psycopg2://botmanager:herbghjx@188.120.245.187/botmanager')


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    lastname = Column(String)
    tg_username = Column(String(30))
    tg_chat_id = Column(Integer)

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, lastname={self.lastname})"


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True)
    event_type = Column(String)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    user = relationship("User", back_populates="events")

    def __repr__(self):
        return f"Event(id={self.id}, event_type={self.event_type}, user_id={self.user.id})"


Base.metadata.create_all(engine)
