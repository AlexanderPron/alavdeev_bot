from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from alavdeev_bot_utils.constants import engine
from alavdeev_bot_utils.bot_models import Base
import sqlalchemy


engine_inst = create_engine(engine)
if not sqlalchemy.inspect(engine_inst).has_table("users"):
    try:
        Base.metadata.create_all(engine_inst)
        print("Таблицы созданы успешно")
    except Exception as e:
        print(f"Что-то не так:\n{e}")
else:
    print("Таблицы уже есть")
