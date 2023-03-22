import configparser
import os.path
from pathlib import Path

# BASE_DIR = os.path.abspath(os.path.dirname(__file__))
BASE_DIR = Path(__file__).resolve().parent.parent
SCOPES = ["https://www.googleapis.com/auth/calendar"]
config = configparser.ConfigParser()
DEV_SETTINGS = os.path.join(BASE_DIR, "config/dev_settings.ini")
SETTINGS = os.path.join(BASE_DIR, "config/settings.ini")
log_file = os.path.join(BASE_DIR, "bot.log")
CURR_SETTINGS = ""
if os.path.isfile(DEV_SETTINGS):
    config.read(DEV_SETTINGS)
    CURR_SETTINGS = DEV_SETTINGS
else:
    config.read(SETTINGS)
    CURR_SETTINGS = SETTINGS
try:
    TOKEN = config["Telegram"]["token"]
    MANAGER_ID = config["Telegram"]["manager_id"]
    GOOGLE_CALENDAR_ID = config["GoogleCalendar"]["calendarId"]
    SERVICE_ACCOUNT_FILE = config["GoogleCalendar"]["service_account_file"]
except Exception:
    print(f"Something wrong with {CURR_SETTINGS}")
    exit()

try:
    DB_HOST = config["DataBase"]["db_host"]
    DB_PORT = config["DataBase"]["db_port"]
    DB_USER = config["DataBase"]["db_user"]
    DB_NAME = config["DataBase"]["db_name"]
    DB_PASS = config["DataBase"]["db_pass"]
except Exception:
    print(f"Something wrong with {CURR_SETTINGS}")
    exit()

engine = f"postgresql+psycopg2://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

SERVICE_ACCOUNT_FILE_PATH = os.path.join(BASE_DIR, "config", SERVICE_ACCOUNT_FILE)

schedule_file_json = os.path.join(BASE_DIR, "data/schedule.json")
WRONG_CANCEL_TEXT = "<b>Консультацию нельзя отменить или перенести менее, чем за 24 часа</b>\n\
Вы можете связаться с Алексеем (@alavdeev) лично и предупредить его об отмене консультации, но в \
этом случае консультация считается проведенной"
about_file = os.path.join(BASE_DIR, "data/about.txt")
DEFAULT_ABOUT_TEXT = "<b>Алексей Авдеев. Психолог-консультант, семейный психолог</b>"
help_file = os.path.join(BASE_DIR, "data/help.txt")
DEFAULT_HELP_TEXT = "Описания работы бота пока нет"

DEFAULT_TIME_ZONE = "Europe/Moscow"

global_event_id = {}
