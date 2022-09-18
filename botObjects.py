from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class UserData:
    """Тип данных для пользователя"""
    id: int = None
    name: str = None
    lastname: str = None
    tg_username: str = None
    tg_chat_id: str = None


@dataclass
class Appointment:
    """Тип данных для объекта записи на консультацию"""

    type: str = None
    mode: str = None
    day: date = None
    time: datetime = None
