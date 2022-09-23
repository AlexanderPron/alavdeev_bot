from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    BigInteger,
    String,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
metadata = Base.metadata


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(30), nullable=False)
    lastname = Column(String)
    tg_username = Column(String(30))
    tg_chat_id = Column(BigInteger)

    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, lastname={self.lastname})"


# class Event(Base):
#     __tablename__ = "event"

#     id = Column(Integer, primary_key=True)
#     event_type = Column(String)
#     user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

#     user = relationship("Users", back_populates="events")

#     def __repr__(self):
#         return f"Event(id={self.id}, event_type={self.event_type}, user_id={self.user.id})"
