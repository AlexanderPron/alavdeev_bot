from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from alavdeev_bot_utils.constants import engine
from alavdeev_bot_utils.bot_models import Base


engine_inst = create_engine(engine)
try:
    Base.metadata.create_all(engine_inst)
    print("Таблицы созданы успешно")
except Exception:
    print("Что-то не так или таблицы уже есть")
