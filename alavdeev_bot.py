import telebot
from telebot.apihelper import ApiTelegramException
from requests.exceptions import (
    ReadTimeout,
    ConnectionError,
)
from urllib3.exceptions import (
    ReadTimeoutError,
    ProtocolError,
)
from http.client import RemoteDisconnected
from telebot_calendar import Calendar, RUSSIAN_LANGUAGE, CallbackData
from telebot.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import datetime
import time
import logging
import json
import configparser
import os.path
import io
import sys
# import validators
from googleCalendar import GoogleCalendar

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SCOPES = ["https://www.googleapis.com/auth/calendar"]
config = configparser.ConfigParser()
DEV_SETTINGS = os.path.join(BASE_DIR, "config/dev_settings.ini")
SETTINGS = os.path.join(BASE_DIR, "config/settings.ini")
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
SERVICE_ACCOUNT_FILE_PATH = os.path.join(BASE_DIR, "config", SERVICE_ACCOUNT_FILE)

schedule_file_json = os.path.join(BASE_DIR, "data/schedule.json")
WRONG_CANCEL_TEXT = "<b>Консультацию нельзя отменить или перенести менее, чем за 24 часа</b>\n\
Вы можете связаться с Алексеем (@alavdeev) лично и предупредить его об отмене консультации, но в \
этом случае консультация считается проведенной"
about_file = os.path.join(BASE_DIR, "data/about.txt")
DEFAULT_ABOUT_TEXT = "<b>Алексей Авдеев. Психолог-консультант, семейный психолог</b>"
help_file = os.path.join(BASE_DIR, "data/help.txt")
DEFAULT_HELP_TEXT = "Описания работы бота пока нет"

bot = telebot.TeleBot(TOKEN, parse_mode=None)
cal = Calendar(language=RUSSIAN_LANGUAGE)
calendar = GoogleCalendar(SERVICE_ACCOUNT_FILE_PATH, GOOGLE_CALENDAR_ID, SCOPES)

calendar_online_single_cb = CallbackData("enroll_calendar_online_single", "action", "year", "month", "day")
calendar_offline_single_cb = CallbackData("enroll_calendar_offline_single", "action", "year", "month", "day")
calendar_online_dual_cb = CallbackData("enroll_calendar_online_dual", "action", "year", "month", "day")
calendar_offline_dual_cb = CallbackData("enroll_calendar_offline_dual", "action", "year", "month", "day")

move_enroll_online_single_cb = CallbackData("move_enroll_online_single", "action", "year", "month", "day")
move_enroll_offline_single_cb = CallbackData("move_enroll_offline_single", "action", "year", "month", "day")
move_enroll_online_dual_cb = CallbackData("move_enroll_online_dual", "action", "year", "month", "day")
move_enroll_offline_dual_cb = CallbackData("move_enroll_offline_dual", "action", "year", "month", "day")

user_data_for_join = {}
global_event_id = {}

logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)
# telebot.logger.setLevel(logging.DEBUG)


# class Appointment:
#     def __init__(self, date_time, duration=60, type="single", mode="online"):
#         self.date_time = date_time
#         self.duration = duration
#         self.type = type
#         self.mode = mode


def convert_schedule_json_to_text(json_file):
    with io.open(json_file, "r", encoding="utf-8") as f:
        text = "<b>Вы можете записаться на консультацию</b>\n"
        json_str = f.read()
        json_obj = json.loads(json_str)
        for sch_type in json_obj.keys():
            if sch_type == "online":
                text += "<u>Онлайн:</u>\n"
                for day in json_obj["online"].keys():
                    if day == "1":
                        text += f"Понедельник {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "2":
                        text += f"Вторник {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "3":
                        text += f"Среда {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "4":
                        text += f"Четверг {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "5":
                        text += f"Пятница {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "6":
                        text += f"Суббота {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "7":
                        text += f"Воскресенье {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
            if sch_type == "offline":
                text += "<u>Очно:</u>\n"
                for day in json_obj["offline"].keys():
                    if day == "1":
                        text += f"Понедельник {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "2":
                        text += f"Вторник {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "3":
                        text += f"Среда {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "4":
                        text += f"Четверг {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "5":
                        text += f"Пятница {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "6":
                        text += f"Суббота {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
                    if day == "7":
                        text += f"Воскресенье {json_obj[sch_type][day]['start']}-{json_obj[sch_type][day]['end']}\n"
        return text


def get_free_time_slots(free_time_list, duration):
    available_start_time_list = []
    for free_time_inteval in free_time_list:
        start = datetime.datetime.strptime(free_time_inteval["start"], "%Y-%m-%dT%H:%M:%S+03:00")
        end = datetime.datetime.strptime(free_time_inteval["end"], "%Y-%m-%dT%H:%M:%S+03:00")
        free_minutes = (end - start).total_seconds() / 60
        if free_minutes < duration:
            continue
        else:
            count = int(free_minutes // 30)
            for i in range(count):
                if (end - (start + i * datetime.timedelta(minutes=30))) < datetime.timedelta(minutes=duration):
                    continue
                else:
                    available_start_time_list.append((start + i * datetime.timedelta(minutes=30)).isoformat())
    if available_start_time_list:
        return available_start_time_list
    else:
        return False


def get_event_type(event):
    """Метод, который возвращает тип события(0,1,2,3 или 4): онлайн/очная/индивидуальная/парная
    0 - событие, не созданное ботом,
    1 - индивидуальная online консультация,
    2 - парная online консультация,
    3 - индивидуальная очная консультация,
    4 - парная очная консультация
    """

    if event["summary"] == "Online консультация":
        event_dt = datetime.datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00")
        event_et = datetime.datetime.strptime(event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00")
        duration_min = (event_et - event_dt).total_seconds() / 60
        if duration_min == 60:
            return 1  # индивидуальная online консультация
        if duration_min == 90:
            return 2  # парная online консультация
    elif event["summary"] == "Очная консультация":
        event_dt = datetime.datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00")
        event_et = datetime.datetime.strptime(event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00")
        duration_min = (event_et - event_dt).total_seconds() / 60
        if duration_min == 60:
            return 3  # индивидуальная очная консультация
        if duration_min == 90:
            return 4  # парная очная консультация
    else:
        return 0  # Событие, не созданное ботом


def add_event(call, appointment_type, appointment_mode, appointment_day, appointment_time, user_data_for_join):
    duration = 60 if appointment_type == "single" else 90
    if appointment_mode == "online":
        appointment_summary = "Online консультация"
        color = "1"
    else:
        appointment_summary = "Очная консультация"
        color = "7"
    t = time.strptime(appointment_time, "%H:%M")
    ts = (
        datetime.datetime.strptime(appointment_day, "%Y-%m-%d") + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min)
    ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
    te = (
        datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
        + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min + duration)
    ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("В начало", callback_data="info_appointment_START"))
    event = calendar.create_event_dict(
        summary=appointment_summary,
        description=f"<b>telegram:</b> @{call.message.chat.username}\n\
<b>Имя:</b> {user_data_for_join[call.message.chat.id]['name']}\n\
<b>Фамилия:</b> {user_data_for_join[call.message.chat.id]['surname']}",
        start=ts,
        end=te,
        colorId=color,
    )
    created_event = calendar.create_event(event)
    return created_event


def send_event_info(call, event):
    appointment_day = event["start"]["dateTime"].split("T")[0]
    time = event["start"]["dateTime"].split("T")[1][:5]
    msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
    e_id = event.get("id")
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Да, раз в неделю", callback_data=f"recurrence_yes_everyweek::{e_id}"),
        InlineKeyboardButton("Да, раз в две недели", callback_data=f"recurrence_yes_onetime2week::{e_id}"),
    )
    keyboard.row(
        InlineKeyboardButton("Нет", callback_data="info_appointment_START"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Вы успешно записались на консультацию {appointment_day} в {time}\n\
Хотите забронировать это время и для будущих трех консультаций?",
        parse_mode="html",
        reply_markup=keyboard,
    )
    bot.send_message(
        MANAGER_ID,
        text=f"<b>{msg_datetime} У Вас новая запись на {event['summary']} на \
{appointment_day} в {time}</b>\n\
{event['description']}",
        parse_mode="html",
    )


def send_move_event_info(call, event):
    appointment_day = event["start"]["dateTime"].split("T")[0]
    time = event["start"]["dateTime"].split("T")[1][:5]
    msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="info_appointment_START"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"Вы успешно записались на консультацию {appointment_day} в {time}",
        parse_mode="html",
        reply_markup=keyboard,
    )
    bot.send_message(
        MANAGER_ID,
        text=f"<b>{msg_datetime} Перенос записи {event['summary']} на \
{appointment_day} в {time}</b>\n\
{event['description']}",
        parse_mode="html",
    )


def send_cancel_event_info(call, event):
    appointment_day = event["start"]["dateTime"].split("T")[0]
    time = event["start"]["dateTime"].split("T")[1][:5]
    msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Назад", callback_data="info_appointment_START"),
    )
    bot.send_message(
        MANAGER_ID,
        text=f"<b>{msg_datetime} Отмена записи {event['summary']} на \
{appointment_day} в {time}</b>\n\
{event['description']}",
        parse_mode="html",
    )


def check_date(date, schedule, appointment_type):
    """Функция возвращает False если день date не содержится в графике режима работы schedule,
    иначе возвращает словарь с начальным и конечным временем. Пример {"start":"10:00","end":"21:00"}"""
    if datetime.datetime.now() > date:
        return False
    day = datetime.datetime.isoweekday(date)
    schedule_json_obj = json.loads(schedule)
    type_schedule = schedule_json_obj.get(appointment_type, {})
    if type_schedule:
        day_time_dict = type_schedule.get(str(day), {})
        return day_time_dict if day_time_dict else False
    else:
        print("В json-расписании нет раздела online")  # TODO Сделать вывод  warning в лог файл
        return False


def get_next_3_weeks_date(start_datetime, end_datetime):
    """Функция получения списка из 3 начальных и конечных дат(со временем) события на следующие 3 недели"""

    lst = []
    for i in range(1, 4):
        dic = {
            "start": (start_datetime + datetime.timedelta(days=i * 7)).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "end": (end_datetime + datetime.timedelta(days=i * 7)).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        }
        lst.append(dic)
    return lst


def get_onetime2week_date(start_datetime, end_datetime):
    """Функция получения списка из 3 начальных и конечных дат(со временем) события один раз в две недели"""

    lst = []
    for i in range(1, 4):
        dic = {
            "start": (start_datetime + datetime.timedelta(days=i * 14)).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
            "end": (end_datetime + datetime.timedelta(days=i * 14)).strftime("%Y-%m-%dT%H:%M:%S+03:00"),
        }
        lst.append(dic)
    return lst


def check_24h(e_id):
    """Функция проверки того, что событие произойдет не ранее чем через 24 часа.
    e_id - id события в google-календаре.
    Возвращает True если событие произойдет более, чем через 24 часа, иначе - False"""

    event_inst = calendar.get_event(e_id)
    event_dt = datetime.datetime.strptime(event_inst["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00")
    return False if (event_dt - datetime.datetime.now()) <= datetime.timedelta(hours=24) else True


@bot.message_handler(commands=["help"])
def help_cmd(message):
    if os.path.isfile(help_file):
        with io.open(help_file, encoding="utf-8") as f:
            help_text = f.read()
        if len(help_text) < 2:
            help_text = DEFAULT_HELP_TEXT
    bot.send_message(
        message.chat.id,
        text=help_text,
        parse_mode="html",
    )


@bot.message_handler(commands=["start"])
def start_cmd(message):
    start_keyboard = InlineKeyboardMarkup()
    start_keyboard.row(
        InlineKeyboardButton("Информация", callback_data="info_get"),
        InlineKeyboardButton("Записаться", callback_data="enroll_start_appointment"),
    )
    start_keyboard.row(
        InlineKeyboardButton("Редактировать запись", callback_data="edit_appointment"),
    )
    if message.from_user.is_bot:
        try:
            bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=message.message_id,
                text="Выберите действие",
                parse_mode="html",
                reply_markup=start_keyboard,
            )
        except ApiTelegramException:
            bot.send_message(
                chat_id=message.chat.id,
                text="Выберите действие",
                parse_mode="html",
                reply_markup=start_keyboard,
            )
    else:
        bot.send_message(
            message.chat.id,
            f"Здравствуйте, <b>{message.from_user.first_name} {message.from_user.last_name}</b>!\n\
Я бот-помощник психолога Алексея Авдеева.\n\
Для записи на консультацию выберите действие и следуйте инструкции, а я добавлю Вашу запись в календарь Алексея.",
            reply_markup=start_keyboard,
            parse_mode="html",
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("info_"))
def show_info(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    if call.data == "info_get":
        keyboard.row(
            InlineKeyboardButton("Обо мне", callback_data="info_about"),
            InlineKeyboardButton("Режим работы", callback_data="info_schedule"),
        )
        keyboard.row(InlineKeyboardButton("В начало", callback_data="info_appointment_START"))
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="<b>Выберите интересующий Вас раздел</b>",
            parse_mode="html",
            reply_markup=keyboard,
        )
    if call.data == "info_about":
        if os.path.isfile(about_file):
            with io.open(about_file, encoding="utf-8") as f:
                about_text = f.read()
            if len(about_text) < 2:
                about_text = DEFAULT_ABOUT_TEXT
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Назад", callback_data="info_get"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=about_text,
            parse_mode="html",
            reply_markup=keyboard,
        )
    if call.data == "info_schedule":
        schedule_text = "\n".join(
            [
                convert_schedule_json_to_text(schedule_file_json),
                "Чтобы узнать ближайшие свободные для записи слоты, перейдите в раздел «Записаться»",
            ]
        )
        keyboard.row(
            InlineKeyboardButton("Записаться", callback_data="enroll_start_appointment"),
        )
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Назад", callback_data="info_get"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=schedule_text,
            parse_mode="html",
            reply_markup=keyboard,
        )
    if call.data == "info_appointment_START":
        start_cmd(call.message)


# ====== Блок прохождения опроса ========
@bot.callback_query_handler(func=lambda call: call.data.startswith("enroll_start_appointment"))
def set_name(call: CallbackQuery):
    global user_data_for_join
    user_data_for_join[call.message.chat.id] = {}
    # msg_instance = bot.send_message(call.message.chat.id, "Укажите Ваше имя")
    msg_instance = bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="Укажите Ваше имя",
        parse_mode="html",
    )
    bot.register_next_step_handler(msg_instance, set_surname)


def set_surname(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Вашу фамилию")
    user_data_for_join[message.chat.id] = {"name": message.text}
    # bot.register_next_step_handler(msg_instance, set_email)
    bot.register_next_step_handler(msg_instance, set_enroll_type)


# def set_email(message):
#     msg_instance = bot.send_message(message.chat.id, "Укажите Ваш e-mail")
#     user_data_for_join[message.chat.id]["surname"] = message.text
#     bot.register_next_step_handler(msg_instance, set_enroll_type)


def set_enroll_type(message):
    # if validators.email(message.text):
    user_data_for_join[message.chat.id]["surname"] = message.text
    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("Индивидуальная онлайн", callback_data="enroll_type_online_single"),
        InlineKeyboardButton("Парная онлайн", callback_data="enroll_type_online_dual"),
    )
    keyboard.row(
        InlineKeyboardButton("Индивидуальная очно", callback_data="enroll_type_offline_single"),
        InlineKeyboardButton("Парная очно", callback_data="enroll_type_offline_dual"),
    )
    bot.send_message(
        chat_id=message.chat.id,
        text="Вы хотите записаться на консультацию онлайн или встретиться с со мной очно?\n\n\
Также хочу предупредить, что очный формат доступен только <b>по вторникам и четвергам с 15:30 до 22:00</b>\n\n\
Длительность индивидуальных консультаций - <b>60 минут</b> \n\
Длительность парных консультаций - <b>90 минут</b>",
        reply_markup=keyboard,
        parse_mode="html",
    )
    # else:
    #     bot.send_message(
    #         message.chat.id,
    #         "Некорректный email. Попробуйте ввести еще раз (example@mail.ru)",
    #     )
    #     bot.register_next_step_handler(message, set_enroll_type)


# ====== Конец блока прохождения опроса ========


@bot.callback_query_handler(func=lambda call: call.data.startswith("enroll_type_"))
def enroll_calendar_show(call: CallbackQuery):
    now = datetime.datetime.now()
    if call.data == "enroll_type_online_single":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите дату, когда Вам удобно было-бы провести индивидуальную online консультацию",
            reply_markup=cal.create_calendar(
                name=calendar_online_single_cb.prefix,
                year=now.year,
                month=now.month,
            ),
        )
    if call.data == "enroll_type_offline_single":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите дату, когда Вам удобно было-бы провести очную индивидуальную консультацию.\n\
Напоминаю, что для очных доступны только вторники и четверги",
            reply_markup=cal.create_calendar(
                name=calendar_offline_single_cb.prefix,
                year=now.year,
                month=now.month,
            ),
        )
    if call.data == "enroll_type_online_dual":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите дату, когда Вам удобно было-бы провести парную online консультацию",
            reply_markup=cal.create_calendar(
                name=calendar_online_dual_cb.prefix,
                year=now.year,
                month=now.month,
            ),
        )
    if call.data == "enroll_type_offline_dual":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите дату, когда Вам удобно было-бы провести очную парную консультацию.\n\
Напоминаю, что для очных доступны только вторники и четверги",
            reply_markup=cal.create_calendar(
                name=calendar_offline_dual_cb.prefix,
                year=now.year,
                month=now.month,
            ),
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_online_single_cb.prefix))
def calendar_online_single(call: CallbackQuery):
    name, action, year, month, day = call.data.split(calendar_online_single_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "online")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 60)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"set_appointment::online_single::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_single"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_single"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_single"),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день приёма нет. Выберите другой день",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_offline_single_cb.prefix))
def calendar_offline_single(call: CallbackQuery):
    name, action, year, month, day = call.data.split(calendar_offline_single_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "offline")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 60)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"set_appointment::offline_single::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_offline_single"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard = InlineKeyboardMarkup()
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_single"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_offline_single"),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день очного приема нет. Выберите вторник или четверг,\
или попробуйте на следующей неделе",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_online_dual_cb.prefix))
def calendar_online_dual(call: CallbackQuery):
    name, action, year, month, day = call.data.split(calendar_online_dual_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "online")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 90)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}", callback_data=f"set_appointment::online_dual::{date}::{hour}:{minutes}"
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_dual"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_dual"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_dual"),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день приёма нет. Выберите другой день",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(calendar_offline_dual_cb.prefix))
def calendar_offline_dual(call: CallbackQuery):
    name, action, year, month, day = call.data.split(calendar_offline_dual_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "offline")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 90)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"set_appointment::offline_dual::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_offline_dual"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online_dual"),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_offline_dual"),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день очного приема нет. Выберите вторник или четверг,\
или попробуйте на следующей неделе",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("set_appointment"))
def set_appointment(call: CallbackQuery):
    appointment_type = call.data.split("::")[1]
    appointment_day = call.data.split("::")[2].split()[0]
    appointment_time = call.data.split("::")[3]
    if appointment_type == "online_single":
        event = add_event(call, "single", "online", appointment_day, appointment_time, user_data_for_join)
        send_event_info(call, event)
    if appointment_type == "offline_single":
        event = add_event(call, "single", "offline", appointment_day, appointment_time, user_data_for_join)
        send_event_info(call, event)
    if appointment_type == "online_dual":
        event = add_event(call, "dual", "online", appointment_day, appointment_time, user_data_for_join)
        send_event_info(call, event)
    if appointment_type == "offline_dual":
        event = add_event(call, "dual", "offline", appointment_day, appointment_time, user_data_for_join)
        send_event_info(call, event)


@bot.callback_query_handler(func=lambda call: call.data.startswith("recurrence_yes"))
def appointment_recurrence_yes(call: CallbackQuery):
    event_id = call.data.split("::")[1]
    event = calendar.get_event(event_id)
    appointment_day = event["start"]["dateTime"].split("T")[0]
    time = event["start"]["dateTime"].split("T")[1][:5]
    msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
    if call.data.split("::")[0] == "recurrence_yes_everyweek":
        created_events_list = calendar.create_multiply_event(
            event,
            get_next_3_weeks_date(
                datetime.datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00"),
                datetime.datetime.strptime(event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00"),
            ),
        )
    elif call.data.split("::")[0] == "recurrence_yes_onetime2week":
        created_events_list = calendar.create_multiply_event(
            event,
            get_onetime2week_date(
                datetime.datetime.strptime(event["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00"),
                datetime.datetime.strptime(event["end"]["dateTime"], "%Y-%m-%dT%H:%M:%S+03:00"),
            ),
        )
    i = 0
    events_info = ""
    for created_event in created_events_list:
        i += 1
        appointment_day = created_event["start"]["dateTime"].split("T")[0]
        time = created_event["start"]["dateTime"].split("T")[1][:5]
        events_info += f"{i}) {appointment_day} в {time}\n"

    keyboard = InlineKeyboardMarkup()
    keyboard.row(
        InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
    )
    if len(created_events_list) > 0:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"Вы успешно записались на консультации:\n{events_info}",
            parse_mode="html",
            reply_markup=keyboard,
        )
        bot.send_message(
            MANAGER_ID,
            text=f"<b>{msg_datetime} У Вас новые записи на {event['summary']}:</b>\n{events_info}\n\
<b>Описание:</b>\n{event['description']}",
            parse_mode="html",
        )
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Записаться", callback_data="enroll_start_appointment"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"К сожаленью, в {time} на предстоящих неделях всё занято.\n\
Но Вы можете выбрать удобное свободное время записываясь на каждую консультацию отдельно",
            parse_mode="html",
            reply_markup=keyboard,
        )


@bot.callback_query_handler(func=lambda call: call.data == "edit_appointment")
def edit_appointment(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if call.message.chat.username:
        events = calendar.get_user_events_list(call.message.chat.username)
        if events:
            for event in events:
                e_summary = event["summary"]
                e_date = str(datetime.datetime.fromisoformat(event["start"]["dateTime"]).date())
                e_time = f'{datetime.datetime.fromisoformat(event["start"]["dateTime"]).strftime("%H:%M")} - \
    {datetime.datetime.fromisoformat(event["end"]["dateTime"]).strftime("%H:%M")}'
                keyboard.add(
                    InlineKeyboardButton(f"{e_summary} {e_date} {e_time}", callback_data=f'event::{event["id"]}')
                )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="<b>Ваши записи:</b>",
                parse_mode="html",
                reply_markup=keyboard,
            )
        else:
            keyboard.row(
                InlineKeyboardButton("Записаться", callback_data="enroll_start_appointment"),
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            )
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="У Вас нет ни одной записи",
                reply_markup=keyboard,
            )
    else:
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="У Вас не задано имя пользователя в профиле telegram.\n\
К сожалению, по этой причине я не могу отобразить Ваши записи.\n\
Пожалуйста, обратитесь к Алексею (@alavdeev) лично для внесения изменений в Ваши записи.\n\
Вы можете указать в настройках telegram Ваше имя пользователя,\
после этого появится возможность просматривать и редактировать Ваши записи",
            parse_mode="html",
            reply_markup=keyboard,
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith("event::"))
def event_detail(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    e_id = call.data.split("::")[1]
    event = calendar.get_event(e_id)
    e_date = str(datetime.datetime.fromisoformat(event["start"]["dateTime"]).date())
    e_time = f'{datetime.datetime.fromisoformat(event["start"]["dateTime"]).strftime("%H:%M")} - \
{datetime.datetime.fromisoformat(event["end"]["dateTime"]).strftime("%H:%M")}'
    keyboard.row(
        InlineKeyboardButton("Отменить", callback_data=f"event_cancel::{e_id}"),
        InlineKeyboardButton("Перезаписаться", callback_data=f"event_edit::{e_id}"),
    )
    keyboard.row(
        InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
        InlineKeyboardButton("Назад", callback_data="edit_appointment"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=f"<b>Дата:</b> {e_date}\n<b>Время:</b> {e_time}\n<b>{event['summary']}</b>\n{event['description']}",
        parse_mode="html",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("event_cancel::"))
def event_cancel(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    e_id = call.data.split("::")[1]
    event = calendar.get_event(e_id)
    if check_24h(e_id):
        calendar.delete_event(e_id)
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Назад", callback_data="edit_appointment"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="<b>Запись отменена</b>",
            parse_mode="html",
            reply_markup=keyboard,
        )
        send_cancel_event_info(call, event)
    else:
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Назад", callback_data="edit_appointment"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=WRONG_CANCEL_TEXT,
            parse_mode="html",
            reply_markup=keyboard,
        )


# ================НАЧАЛО блока переноса записи====================


@bot.callback_query_handler(func=lambda call: call.data.startswith("event_edit::"))
def move_enroll_calendar_show(call: CallbackQuery):
    now = datetime.datetime.now()
    e_id = call.data.split("::")[1]
    if check_24h(e_id):
        global global_event_id
        global_event_id[call.message.chat.id] = e_id
        event = calendar.get_event(e_id)
        event_type = get_event_type(event)
        if event_type == 1:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Выберите новую дату, когда Вам удобно было-бы провести индивидуальную online консультацию",
                reply_markup=cal.create_calendar(
                    name=move_enroll_online_single_cb.prefix,
                    year=now.year,
                    month=now.month,
                ),
            )
        if event_type == 3:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Выберите дату, когда Вам удобно было-бы провести очную индивидуальную консультацию.\n\
Напоминаю, что для очных доступны только вторники и четверги",
                reply_markup=cal.create_calendar(
                    name=move_enroll_offline_single_cb.prefix,
                    year=now.year,
                    month=now.month,
                ),
            )
        if event_type == 2:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Выберите дату, когда Вам удобно было-бы провести парную online консультацию",
                reply_markup=cal.create_calendar(
                    name=move_enroll_online_dual_cb.prefix,
                    year=now.year,
                    month=now.month,
                ),
            )
        if event_type == 4:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Выберите дату, когда Вам удобно было-бы провести очную парную консультацию.\n\
Напоминаю, что для очных доступны только вторники и четверги",
                reply_markup=cal.create_calendar(
                    name=move_enroll_offline_dual_cb.prefix,
                    year=now.year,
                    month=now.month,
                ),
            )
    else:
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Назад", callback_data="edit_appointment"),
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=WRONG_CANCEL_TEXT,
            parse_mode="html",
            reply_markup=keyboard,
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith(move_enroll_online_single_cb.prefix))
def move_enroll_online_single(call: CallbackQuery):
    name, action, year, month, day = call.data.split(move_enroll_online_single_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "online")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 60)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"move_appointment::online_single::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton(
                    "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                ),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день приёма нет. Выберите другой день",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(move_enroll_offline_single_cb.prefix))
def move_enroll_offline_single(call: CallbackQuery):
    name, action, year, month, day = call.data.split(move_enroll_offline_single_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "offline")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 60)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"move_appointment::offline_single::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton(
                    "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                ),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день очного приема нет. Выберите вторник или четверг,\
или попробуйте на следующей неделе",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(move_enroll_online_dual_cb.prefix))
def move_enroll_online_dual(call: CallbackQuery):
    name, action, year, month, day = call.data.split(move_enroll_online_dual_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "online")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 90)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"move_appointment::online_dual::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton(
                    "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                ),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день приёма нет. Выберите другой день",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(move_enroll_offline_dual_cb.prefix))
def move_enroll_offline_dual(call: CallbackQuery):
    name, action, year, month, day = call.data.split(move_enroll_offline_dual_cb.sep)
    date = cal.calendar_query_handler(
        bot=bot,
        call=call,
        name=name,
        action=action,
        year=year,
        month=month,
        day=day,
    )
    if action == "DAY":
        with io.open(schedule_file_json, "r", encoding="utf-8") as f:
            schedule = f.read()
        available_time_dict = check_date(date, schedule, "offline")
        if available_time_dict:
            free_time_list = calendar.get_free_daytime(date, available_time_dict["start"], available_time_dict["end"])
            free_slots = get_free_time_slots(free_time_list, 90)
            keyboard = InlineKeyboardMarkup()
            if free_slots:
                for slot in free_slots:
                    hour = slot.split("T")[1].split(":")[0]
                    minutes = slot.split("T")[1].split(":")[1]
                    keyboard.add(
                        InlineKeyboardButton(
                            f"{hour}:{minutes}",
                            callback_data=f"move_appointment::offline_dual::{date}::{hour}:{minutes}",
                        )
                    )
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Выберите время, на которое вы бы хотели записаться",
                    reply_markup=keyboard,
                )
            else:
                keyboard.row(
                    InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                    InlineKeyboardButton(
                        "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                    ),
                )
                bot.send_message(
                    call.message.chat.id,
                    "Извините, в этот день свободного для записи времени нет. Выберите другой день",
                    reply_markup=keyboard,
                )
        else:
            keyboard = InlineKeyboardMarkup()
            keyboard.row(
                InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
                InlineKeyboardButton(
                    "Выбрать другую дату", callback_data=f"event_edit::{global_event_id[call.message.chat.id]}"
                ),
            )
            bot.send_message(
                call.message.chat.id,
                "Извините, в этот день очного приема нет. Выберите вторник или четверг,\
или попробуйте на следующей неделе",
                reply_markup=keyboard,
            )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith("move_appointment"))
def move_appointment(call: CallbackQuery):
    appointment_type = call.data.split("::")[1]
    appointment_day = call.data.split("::")[2].split()[0]
    appointment_time = call.data.split("::")[3]
    if appointment_type == "online_single":
        event = calendar.get_event(global_event_id[call.message.chat.id])
        t = time.strptime(appointment_time, "%H:%M")
        ts = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        te = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min + 60)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        event["start"]["dateTime"] = ts
        event["end"]["dateTime"] = te
        calendar.event_edit(global_event_id[call.message.chat.id], event)
        send_move_event_info(call, event)
    if appointment_type == "offline_single":
        event = calendar.get_event(global_event_id[call.message.chat.id])
        t = time.strptime(appointment_time, "%H:%M")
        ts = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        te = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min + 60)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        event["start"]["dateTime"] = ts
        event["end"]["dateTime"] = te
        calendar.event_edit(global_event_id[call.message.chat.id], event)
        send_move_event_info(call, event)
    if appointment_type == "online_dual":
        event = calendar.get_event(global_event_id[call.message.chat.id])
        t = time.strptime(appointment_time, "%H:%M")
        ts = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        te = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min + 90)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        event["start"]["dateTime"] = ts
        event["end"]["dateTime"] = te
        calendar.event_edit(global_event_id[call.message.chat.id], event)
        send_move_event_info(call, event)
    if appointment_type == "offline_dual":
        event = calendar.get_event(global_event_id[call.message.chat.id])
        t = time.strptime(appointment_time, "%H:%M")
        ts = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        te = (
            datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
            + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min + 90)
        ).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        event["start"]["dateTime"] = ts
        event["end"]["dateTime"] = te
        calendar.event_edit(global_event_id[call.message.chat.id], event)
        send_move_event_info(call, event)


# =============КОНЕЦ блока переноса записи=======================


def main():
    try:
        while True:
            try:
                bot.polling(non_stop=True)
            except (
                ReadTimeout,
                ReadTimeoutError,
                TimeoutError,
                RemoteDisconnected,
                ProtocolError,
                ConnectionError,
            ):
                time.sleep(5)
                continue
    except KeyboardInterrupt:
        sys.exit()
    # try:
    #     bot.polling(non_stop=True)
    # except (
    #     ReadTimeout,
    #     ReadTimeoutError,
    #     TimeoutError,
    #     RemoteDisconnected,
    #     ProtocolError,
    #     ConnectionError,
    # ):
    #     time.sleep(5)


if __name__ == "__main__":
    main()
