from alavdeev_bot_utils.constants import (
    log_file,
    MANAGER_ID,
)
from alavdeev_bot import bot, calendar
from alavdeev_bot_utils.botObjects import UserData
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import datetime
import time
import json
import io


def add_log(msg_text, msg_type="info", log_file=log_file):
    """Функция добавления лога msg_text со статусом msg_type в файл log_file"""

    with io.open(log_file, "a", encoding="utf-8") as f:
        record = f'\n[{datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")}] {msg_type.upper()}: {msg_text}'
        f.write(record)


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
        start = datetime.datetime.strptime(free_time_inteval["start"], "%Y-%m-%dT%H:%M:%S%z")
        end = datetime.datetime.strptime(free_time_inteval["end"], "%Y-%m-%dT%H:%M:%S%z")
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

    if event["extendedProperties"]["private"]["type"] == "single_online":
        return 1  # индивидуальная online консультация
    if event["extendedProperties"]["private"]["type"] == "dual_online":
        return 2  # парная online консультация
    if event["extendedProperties"]["private"]["type"] == "single_offline":
        return 3  # индивидуальная очная консультация
    if event["extendedProperties"]["private"]["type"] == "dual_offline":
        return 4  # парная очная консультация
    else:
        return 0  # Событие, не созданное ботом


def type_to_rus(eng_type, case="nominative"):
    """
    Функция для преобразования ангийского названия типа записи в русское.
    Например, single_online --> индивидуальня online
    """

    txt = ""
    # Именительный падеж
    if case == "nominative":
        if eng_type == "single_online":
            txt = "индивидуальная online"
        if eng_type == "dual_online":
            txt = "парная online"
        if eng_type == "single_offline":
            txt = "индивидуальная очная"
        if eng_type == "dual_offline":
            txt = "парная очная"
    # Винительный падеж
    if case == "accusative":
        if eng_type == "single_online":
            txt = "индивидуальную online"
        if eng_type == "dual_online":
            txt = "парную online"
        if eng_type == "single_offline":
            txt = "индивидуальную очную"
        if eng_type == "dual_offline":
            txt = "парную очную"
    return txt


def add_event(call, appointment_type, appointment_mode, appointment_day, appointment_time, user: UserData):
    duration = 60 if appointment_type == "single" else 90
    appointment_summary = f"{user.name} \
{user.lastname}"
    t = time.strptime(appointment_time, "%H:%M")
    ts = (
        datetime.datetime.strptime(appointment_day, "%Y-%m-%d") + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min)
    ).strftime("%Y-%m-%dT%H:%M:%S%z")
    te = (
        datetime.datetime.strptime(appointment_day, "%Y-%m-%d")
        + datetime.timedelta(hours=t.tm_hour, minutes=t.tm_min + duration)
    ).strftime("%Y-%m-%dT%H:%M:%S%z")

    if appointment_type == "single" and appointment_mode == "online":
        color = "1"
        event_type = "single_online"
    if appointment_type == "single" and appointment_mode == "offline":
        color = "7"
        event_type = "single_offline"
    if appointment_type == "dual" and appointment_mode == "online":
        color = "1"
        event_type = "dual_online"
    if appointment_type == "dual" and appointment_mode == "offline":
        color = "7"
        event_type = "dual_offline"

    event = calendar.create_event_dict(
        event_type=event_type,
        summary=appointment_summary,
        description=f"<b>telegram:</b> @{user.tg_username}\n\
<b>Имя:</b> {user.name}\n\
<b>Фамилия:</b> {user.lastname}",
        start=ts,
        end=te,
        colorId=color,
    )
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton("В начало", callback_data="info_appointment_START"))
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
        InlineKeyboardButton("Нет", callback_data=f"info_appointment_START::{appointment_day}::{time}"),
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
        text=f'<b>{msg_datetime} У Вас новая запись на \
{type_to_rus(event["extendedProperties"]["private"]["type"], case="accusative")} \
консультацию на {appointment_day} в {time}</b>\n{event["description"]}',
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
        text=f'<b>{msg_datetime} Перенос записи на \
{type_to_rus(event["extendedProperties"]["private"]["type"], case="accusative")} консультацию на \
{appointment_day} в {time}</b>\n{event["description"]}',
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
        text=f'<b>{msg_datetime} Отмена записи на \
{type_to_rus(event["extendedProperties"]["private"]["type"], case="accusative")} консультацию \
{appointment_day} в {time}</b>\n{event["description"]}',
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
        add_log(f"В json-расписании(файл {schedule}) нет раздела {type_schedule}", "warning")
        return False


def get_next_3_weeks_date(start_datetime, end_datetime):
    """Функция получения списка из 3 начальных и конечных дат(со временем) события на следующие 3 недели"""

    lst = []
    for i in range(1, 4):
        dic = {
            "start": (start_datetime + datetime.timedelta(days=i * 7)).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "end": (end_datetime + datetime.timedelta(days=i * 7)).strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        lst.append(dic)
    return lst


def get_onetime2week_date(start_datetime, end_datetime):
    """Функция получения списка из 3 начальных и конечных дат(со временем) события один раз в две недели"""

    lst = []
    for i in range(1, 4):
        dic = {
            "start": (start_datetime + datetime.timedelta(days=i * 14)).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "end": (end_datetime + datetime.timedelta(days=i * 14)).strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        lst.append(dic)
    return lst


def check_24h(e_id):
    """Функция проверки того, что событие произойдет не ранее чем через 24 часа.
    e_id - id события в google-календаре.
    Возвращает True если событие произойдет более, чем через 24 часа, иначе - False"""

    event_inst = calendar.get_event(e_id)
    event_dt = datetime.datetime.strptime(event_inst["start"]["dateTime"], "%Y-%m-%dT%H:%M:%S%z")
    return False if (event_dt - datetime.datetime.now()) <= datetime.timedelta(hours=24) else True
