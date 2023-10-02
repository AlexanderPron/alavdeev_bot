from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from alavdeev_bot_utils.constants import engine
from alavdeev_bot_utils.bot_models import Base
import sqlalchemy


engine_inst = create_engine(engine)
try:
    if not sqlalchemy.inspect(engine).has_table("USERS"):
        Base.metadata.create_all(engine_inst)
        print("Таблицы созданы успешно")
    else:
        print("Таблицы уже есть")
except Exception as e:
    print(f"Что-то не так:\n{e}")
