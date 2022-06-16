from zoneinfo import available_timezones
import telebot
from telebot_calendar import Calendar, RUSSIAN_LANGUAGE, CallbackData
from telebot.types import (
    ReplyKeyboardRemove,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import datetime
import logging
import json
import configparser
import os.path
import io
import validators
from googleCalendar import GoogleCalendar


SCOPES = ["https://www.googleapis.com/auth/calendar"]
calendarId = "alexpronin85@gmail.com"
SERVICE_ACCOUNT_FILE = "./avd-bot-87f99ff81853.json"
EVERYDAY_2_TIMES = "RRULE:FREQ=DAILY;COUNT=2"

DEV_SETTINGS = "./dev_settings.ini"
SETTINGS = "./settings.ini"
CURR_SETTINGS = ""
schedule_file = "./schedule.txt"
DEFAULT_SCHEDULE_TEXT = "<b>Режим работы уточняйте у врача</b>"
about_file = "./about.txt"
DEFAULT_ABOUT_TEXT = "<b>Алексей Авдеев. Психолог-консультант, семейный психолог</b>"
user_data_for_join = {}
config = configparser.ConfigParser()
if os.path.isfile(DEV_SETTINGS):
    config.read(DEV_SETTINGS)
    CURR_SETTINGS = DEV_SETTINGS
else:
    config.read(SETTINGS)
    CURR_SETTINGS = SETTINGS
try:
    TOKEN = config["Telegram"]["token"]
    MANAGER_ID = config["Telegram"]["manager_id"]
except Exception:
    print(f"Something wrong with {CURR_SETTINGS}")
    exit()
bot = telebot.TeleBot(TOKEN, parse_mode=None)
cal = Calendar(language=RUSSIAN_LANGUAGE)
calendar = GoogleCalendar(SERVICE_ACCOUNT_FILE, calendarId, SCOPES)
enroll_calendar_online = CallbackData("enroll_calendar_online", "action", "year", "month", "day")
enroll_calendar_offline = CallbackData("enroll_calendar_offline", "action", "year", "month", "day")
user_data_for_join = {}

logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)
# telebot.logger.setLevel(logging.DEBUG)


def get_free_time_slots(free_time_list, duration):
    available_start_time_list = []
    for free_time_inteval in free_time_list:
        start = datetime.datetime.strptime(free_time_inteval["start"], "%Y-%m-%dT%H:%M:%S+03:00")
        end = datetime.datetime.strptime(free_time_inteval["end"], "%Y-%m-%dT%H:%M:%S+03:00")
        free_minutes = (end - start).total_seconds() / 60
        if (free_minutes < duration):
            continue
        else:
            count = int(free_minutes // duration)
            for i in range(count):
                available_start_time_list.append((start + i * datetime.timedelta(minutes=duration)).isoformat())
    if available_start_time_list:
        return available_start_time_list
    else:
        return False


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, "Тут будет описание команд и возможностей бота")


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
        bot.send_message(
            message.chat.id,
            "Выберите действие",
            reply_markup=start_keyboard,
        )
    else:
        bot.send_message(
            message.chat.id,
            f"Здравствуйте, <b>{message.from_user.first_name} {message.from_user.last_name}</b>! \
Я бот-помощник психолога Алексея Авдеева. Для записи на консультацию напишите Ваше имя и фамилию. \
Я добавлю Вашу запись в календарь Алексея.",
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
        if os.path.isfile(schedule_file):
            with io.open(schedule_file, encoding="utf-8") as f:
                schedule_text = f.read()
            if len(schedule_text) < 2:
                schedule_text = DEFAULT_SCHEDULE_TEXT
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
    msg_instance = bot.send_message(call.message.chat.id, "Укажите Ваше имя")
    bot.register_next_step_handler(msg_instance, set_surname)


def set_surname(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Вашу фамилию")
    user_data_for_join[message.chat.id] = {"name": message.text}
    bot.register_next_step_handler(msg_instance, set_email)


def set_email(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Ваш e-mail")
    user_data_for_join[message.chat.id]["surname"] = message.text
    bot.register_next_step_handler(msg_instance, set_enroll_type)


def set_enroll_type(message):
    if validators.email(message.text):
        keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("Онлайн", callback_data="enroll_type_online"),
            InlineKeyboardButton("Очно", callback_data="enroll_type_offline"),
        )
        bot.send_message(
            chat_id=message.chat.id,
            text="Вы хотите записаться на консультацию online или встретиться с врачом в очном формате?",
            reply_markup=keyboard,
        )
        user_data_for_join[message.chat.id]["email"] = message.text
    else:
        bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё раз! (example@mail.ru)")
        bot.register_next_step_handler(message, set_enroll_type)


# ====== Конец блока прохождения опроса ========


@bot.callback_query_handler(func=lambda call: call.data.startswith("enroll_type_"))
def enroll_calendar_show(call: CallbackQuery):
    now = datetime.datetime.now()
    if call.data == "enroll_type_online":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите дату, когда Вам удобно было-бы провести online консультацию",
            reply_markup=cal.create_calendar(
                name=enroll_calendar_online.prefix,
                year=now.year,
                month=now.month,
            ),
        )
    if call.data == "enroll_type_offline":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Выберите дату, когда Вам удобно было-бы провести offline консультацию",
            reply_markup=cal.create_calendar(
                name=enroll_calendar_offline.prefix,
                year=now.year,
                month=now.month,
            ),
        )


@bot.callback_query_handler(func=lambda call: call.data.startswith(enroll_calendar_online.prefix))
def calendar_online(call: CallbackQuery):
    name, action, year, month, day = call.data.split(enroll_calendar_online.sep)
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
        free_time_list = calendar.get_free_daytime(date, "10:00", "18:00")
        # free_time_list = calendar.get_free_daytime(date)
        free_slots = get_free_time_slots(free_time_list, 60)
        print(f"free list - {str(free_time_list)}")
        print(free_slots)
        keyboard = InlineKeyboardMarkup()
        for slot in free_slots:
            hour = slot.split("T")[1].split(":")[0]
            minutes = slot.split("T")[1].split(":")[1]
            keyboard.add(
                InlineKeyboardButton(
                    f"{hour}:{minutes}",
                    callback_data=f"set_appointment::{hour}-{minutes}"
                )
            )
        keyboard.row(
            InlineKeyboardButton("В начало", callback_data="info_appointment_START"),
            InlineKeyboardButton("Выбрать другую дату", callback_data="enroll_type_online"),
        )
        bot.send_message(
            call.message.chat.id,
            "Выберите время, на которое вы бы хотели записаться",
            reply_markup=keyboard,
        )


#         msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
#         keyboard = InlineKeyboardMarkup()
#         keyboard.row(InlineKeyboardButton("В начало", callback_data="info_appointment_START"))
#         event = calendar.create_event_dict(
#             summary="Online консультация",
#             description=f"<b>telegram:</b> @{call.message.chat.username}\n\
# <b>Имя:</b> {user_data_for_join[call.message.chat.id]['name']}\n\
# <b>Фамилия:</b> {user_data_for_join[call.message.chat.id]['surname']}\n\
# <b>Email:</b> {user_data_for_join[call.message.chat.id]['email']}",
#             # start=str(datetime.datetime.now()),
#             # end=str(datetime.datetime.fromtimestamp(datetime.datetime.timestamp(datetime.datetime.now()) + 3600)),
#             start='2022-06-14T11:00:00+03:00',
#             end='2022-06-14T12:00:00+03:00',
#             colorId='1',
#             recurrence=EVERYDAY_2_TIMES,
#         )
#         calendar.create_event(event)
#         bot.send_message(
#             call.message.chat.id,
#             f"Вы успешно записались на online консультацию на {date.strftime('%d.%m.%Y')}",
#             reply_markup=keyboard,
#         )
#         bot.send_message(
#             MANAGER_ID,
#             text=f"<b>{msg_datetime} У Вас новая запись на online консультацию на {date.strftime('%d.%m.%Y')}</b>\n \
# <b>telegram:</b> @{call.message.chat.username}\n \
# <b>Имя:</b> {user_data_for_join[call.message.chat.id]['name']}\n \
# <b>Фамилия:</b> {user_data_for_join[call.message.chat.id]['surname']}\n \
# <b>Email:</b> {user_data_for_join[call.message.chat.id]['email']}",
#             parse_mode="html",
#         )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data.startswith(enroll_calendar_offline.prefix))
def calendar_offline(call: CallbackQuery):
    name, action, year, month, day = call.data.split(enroll_calendar_offline.sep)
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
        msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("В начало", callback_data="info_appointment_START"))
        event = calendar.create_event_dict(
            summary="Offline консультация",
            description=f"<b>telegram:</b> @{call.message.chat.username}\n \
<b>Имя:</b> {user_data_for_join[call.message.chat.id]['name']}\n \
<b>Фамилия:</b> {user_data_for_join[call.message.chat.id]['surname']}\n \
<b>Email:</b> {user_data_for_join[call.message.chat.id]['email']}",
            # start=str(datetime.datetime.now()),
            # end=str(datetime.datetime.fromtimestamp(datetime.datetime.timestamp(datetime.datetime.now()) + 3600)),
            start='2022-06-14T11:00:00+03:00',
            end='2022-06-14T12:00:00+03:00',
            colorId='7',
            recurrence=EVERYDAY_2_TIMES,
        )
        calendar.create_event(event)
        bot.send_message(
            call.message.chat.id,
            f"Вы успешно записались на offline консультацию на {date.strftime('%d.%m.%Y')}",
            reply_markup=keyboard,
        )
        bot.send_message(
            MANAGER_ID,
            text=f"<b>{msg_datetime} У Вас новая запись на offline консультацию на {date.strftime('%d.%m.%Y')}</b>\n \
<b>telegram:</b> @{call.message.chat.username}\n \
<b>Имя:</b> {user_data_for_join[call.message.chat.id]['name']}\n \
<b>Фамилия:</b> {user_data_for_join[call.message.chat.id]['surname']}\n \
<b>Email:</b> {user_data_for_join[call.message.chat.id]['email']}",
            parse_mode="html",
        )
    elif action == "CANCEL":
        start_cmd(call.message)


@bot.callback_query_handler(func=lambda call: call.data == "edit_appointment")
def edit_appointment(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup(row_width=1)
    events = calendar.get_user_events_list(call.message.chat.username)
    if events:
        for event in events:
            e_summary = event["summary"]
            e_date = str(datetime.datetime.fromisoformat(event["start"]["dateTime"]).date())
            e_time = f'{datetime.datetime.fromisoformat(event["start"]["dateTime"]).strftime("%H:%M")} - \
{datetime.datetime.fromisoformat(event["end"]["dateTime"]).strftime("%H:%M")}'
            keyboard.add(InlineKeyboardButton(f'{e_summary} {e_date} {e_time}', callback_data=f'event::{event["id"]}'))
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
        bot.send_message(
            call.message.chat.id,
            "У Вас нет ни одной записи",
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
    calendar.delete_event(e_id)
    keyboard.row(
        InlineKeyboardButton("В начало", callback_data="enroll_start_appointment"),
        InlineKeyboardButton("Назад", callback_data="edit_appointment"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="<b>Запись отменена</b>",
        parse_mode="html",
        reply_markup=keyboard,
    )


@bot.callback_query_handler(func=lambda call: call.data.startswith("event_edit::"))
def event_edit(call: CallbackQuery):
    keyboard = InlineKeyboardMarkup()
    e_id = call.data.split("::")[1]
    event = calendar.get_event(e_id)
    event["start"]["dateTime"] = "2022-06-18T10:30:00+03:00"
    event["end"]["dateTime"] = "2022-06-18T11:30:00+03:00"
    calendar.event_edit(e_id, event)
    keyboard.row(
        InlineKeyboardButton("В начало", callback_data="enroll_start_appointment"),
        InlineKeyboardButton("Назад", callback_data="edit_appointment"),
    )
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="<b>Вы успешно перезаписались</b>",
        parse_mode="html",
        reply_markup=keyboard,
    )


def main():
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
