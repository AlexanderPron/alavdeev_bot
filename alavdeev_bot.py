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
import validators

DEV_SETTINGS = "./dev_settings.ini"
SETTINGS = "./settings.ini"
CURR_SETTINGS = ""
MANAGER_ID = "5174228279"
config = configparser.ConfigParser()
if os.path.isfile(DEV_SETTINGS):
    config.read(DEV_SETTINGS)
    CURR_SETTINGS = DEV_SETTINGS
else:
    config.read(SETTINGS)
    CURR_SETTINGS = SETTINGS
try:
    TOKEN = config["Telegram"]["token"]
except Exception:
    print(f"Something wrong with {CURR_SETTINGS}")
    exit()
bot = telebot.TeleBot(TOKEN, parse_mode=None)
cal = Calendar(language=RUSSIAN_LANGUAGE)
enroll_calendar_online = CallbackData("enroll_calendar_online", "action", "year", "month", "day")
enroll_calendar_offline = CallbackData("enroll_calendar_offline", "action", "year", "month", "day")
prev_callback_data_enroll = ""

logger = telebot.logger
telebot.logger.setLevel(logging.WARNING)


@bot.callback_query_handler(func=lambda call: call.data.startswith("enroll_start_shelter"))
def set_name(call: CallbackQuery):
    global user_data_for_join
    user_data_for_join = {}
    msg_instance = bot.send_message(call.message.chat.id, "Укажите Ваше имя")
    bot.register_next_step_handler(msg_instance, set_surname)


def set_surname(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Вашу фамилию")
    user_data_for_join["name"] = message.text
    bot.register_next_step_handler(msg_instance, set_email)


def set_email(message):
    msg_instance = bot.send_message(message.chat.id, "Укажите Ваш e-mail")
    user_data_for_join["surname"] = message.text
    bot.register_next_step_handler(msg_instance, set_enroll_type)


def set_enroll_type(message):
    if validators.email(message.text):
        keyboard = keyboard = InlineKeyboardMarkup()
        keyboard.row(
            InlineKeyboardButton("Online", callback_data="enroll_type_online"),
            InlineKeyboardButton("Offline", callback_data="enroll_type_offline"),
        )
        bot.send_message(
            chat_id=message.chat.id,
            text="Вы хотите записаться на консультацию online или встретиться с врачом в офисе (offline)?",
            reply_markup=keyboard,
        )
        user_data_for_join["email"] = message.text
    else:
        bot.send_message(message.chat.id, "Не корректный email!! Попробуйте ввести ещё разок! (example@mail.ru)")
        bot.register_next_step_handler(message, set_enroll_type)


@bot.message_handler(commands=["help"])
def help_cmd(message):
    bot.reply_to(message, "Тут будет описание команд и возможностей бота")


@bot.message_handler(commands=["start"])
def start_cmd(message):
    start_keyboard = InlineKeyboardMarkup(row_width=2)
    start_keyboard.row(
        InlineKeyboardButton("Инфо", callback_data="info_get"),
        InlineKeyboardButton("Записаться", callback_data="enroll_start_shelter"),
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
    keyboard.row(InlineKeyboardButton("В начало", callback_data="info_shelter_START"))
    callback_data_info_list = []
    if call.data == "info_get":
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="Тут будет информация о докторе",
            reply_markup=keyboard,
        )
    if call.data == "info_shelter_START":
        start_cmd(call.message)


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
        msg_datetime = datetime.datetime.fromtimestamp(call.message.date)
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("В начало", callback_data="info_shelter_START"))
        bot.send_message(
            call.message.chat.id,
            f"Вы успешно записались на online консультацию на {date.strftime('%d.%m.%Y')}",
            reply_markup=keyboard,
        )
        bot.send_message(
            MANAGER_ID,
            text=f"{msg_datetime} У Вас новая запись (id={call.message.chat.id} username={call.message.chat.username} данные: {str(user_data_for_join)}) \
на online консультацию на {date.strftime('%d.%m.%Y')}",
        )
        print(f"{enroll_calendar_online}: Day: {date.strftime('%d.%m.%Y')}")
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
        keyboard.row(InlineKeyboardButton("В начало", callback_data="info_shelter_START"))
        bot.send_message(
            call.message.chat.id,
            f"Вы успешно записались на offline консультацию на {date.strftime('%d.%m.%Y')}",
            reply_markup=keyboard,
        )
        bot.send_message(
            MANAGER_ID,
            text=f"{msg_datetime} У Вас новая запись (id={call.message.chat.id} username={call.message.chat.username} данные: {str(user_data_for_join)}) \
на offline консультацию на {date.strftime('%d.%m.%Y')}",
        )
        print(f"{enroll_calendar_offline}: Day: {date.strftime('%d.%m.%Y')}")
    elif action == "CANCEL":
        start_cmd(call.message)


def main():
    bot.polling(non_stop=True)


if __name__ == "__main__":
    main()
