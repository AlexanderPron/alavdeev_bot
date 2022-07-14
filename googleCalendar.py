import datetime
from datetime import date
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import googleapiclient
from google.oauth2 import service_account


class GoogleCalendar(object):
    def __init__(self, service_file_path, calendarId, scope):
        self.service_file_path = service_file_path
        self.calendarId = calendarId
        self.scope = scope
        credentials = service_account.Credentials.from_service_account_file(self.service_file_path, scopes=self.scope)
        self.service = googleapiclient.discovery.build("calendar", "v3", credentials=credentials)

    # создание словаря с информацией о событии
    def create_event_dict(self, summary, description, start, end, **kwargs):
        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start,
            },
            "end": {
                "dateTime": end,
            },
        }
        if "colorId" in kwargs:
            event["colorId"] = kwargs["colorId"]
        if "recurrence" in kwargs:
            event["recurrence"] = kwargs["recurrence"]
        return event

    def create_event(self, event):
        e = self.service.events().insert(calendarId=self.calendarId, body=event).execute()
        print("Event created: %s" % (e.get("id")))
        return e

    def get_user_events_list(self, tg_username):
        now = datetime.datetime.now().isoformat() + "+03:00"
        events_result = (
            self.service.events()
            .list(
                calendarId=self.calendarId,
                timeMin=now,
                singleEvents=True,
                orderBy="startTime",
                q=f"@{str(tg_username)}",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            return False
        return events

    def get_event(self, e_id):
        return self.service.events().get(calendarId=self.calendarId, eventId=e_id).execute()

    def get_day_events(self, day):
        day_0 = day.strftime("%Y-%m-%dT%H:%M:%S+03:00")
        day_24 = (day + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        events_result = (
            self.service.events()
            .list(
                calendarId=self.calendarId,
                timeMin=day_0,
                timeMax=day_24,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])
        if not events:
            return False
        return events

    def get_free_daytime(self, day, time_start="0:0", time_end="23:59"):
        """Метод для получения свободного времени в определённый день.
        Параметр time_start устанавливает начальное время (например, начало рабочего дня)
        Параметр time_end устанавливает конечное время (например, конец рабочего дня ).
        Если параметры time_start и time_end не заданы, то берутся полные сутки"""

        empty_time_list = []
        t1 = time.strptime(time_start, "%H:%M")  # TODO Сделать проверку на коректность ввода времени try except
        t2 = time.strptime(time_end, "%H:%M")
        ts = (day + datetime.timedelta(hours=t1.tm_hour, minutes=t1.tm_min)).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        te = (day + datetime.timedelta(hours=t2.tm_hour, minutes=t2.tm_min)).strftime("%Y-%m-%dT%H:%M:%S+03:00")
        query_body = {"timeMin": ts, "timeMax": te, "timeZone": "Europe/Moscow", "items": [{"id": self.calendarId}]}
        busy_info = self.service.freebusy().query(body=query_body).execute()
        busy_time_list = busy_info.get("calendars").get(self.calendarId).get("busy", [])
        dic = {}
        if busy_time_list:
            if busy_time_list[0]["start"] > ts:
                empty_time_list.append({"start": ts, "end": busy_time_list[0]["start"]})
            i = 0
            for i in range(len(busy_time_list) - 1):
                dic["start"] = busy_time_list[i]["end"]
                dic["end"] = busy_time_list[i + 1]["start"]
                empty_time_list.append({"start": dic["start"], "end": dic["end"]})
            if busy_time_list[-1]["end"] < te:
                empty_time_list.append({"start": busy_time_list[-1]["end"], "end": te})
        else:
            empty_time_list.append({"start": ts, "end": te})
        return empty_time_list

    def delete_event(self, e_id):
        return self.service.events().delete(calendarId=self.calendarId, eventId=e_id).execute()

    def event_edit(self, e_id, new_event):
        return self.service.events().update(calendarId=self.calendarId, eventId=e_id, body=new_event).execute()

    def get_recurrence_events(self, e_id):
        return self.service.events().instances(calendarId=self.calendarId, eventId=e_id).execute()

    def check_time(self, event):
        ts = "2022-07-18T00:30:00+03:00"  # event["start"]["dateTime"]
        te = "2022-07-23T23:30:00+03:00"  # event["end"]["dateTime"]
        query_body = {"timeMin": ts, "timeMax": te, "timeZone": "Europe/Moscow", "items": [{"id": self.calendarId}]}
        busy_info = self.service.freebusy().query(body=query_body).execute()
        print(f"busy_info --- {busy_info}")
        if busy_info.get("calendars").get(self.calendarId).get("busy", []):
            return False
        else:
            return True
