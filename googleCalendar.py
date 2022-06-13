import datetime
from datetime import date
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
        self.service = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)

    # создание словаря с информацией о событии
    def create_event_dict(self, summary, description, start, end, **kwargs):
        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start,
            },
            'end': {
                'dateTime': end,
            },
        }
        if 'colorId' in kwargs:
            event['colorId'] = kwargs['colorId']
        if 'recurrence' in kwargs:
            event['recurrence'] = kwargs['recurrence']
        return event

    def create_event(self, event):
        e = self.service.events().insert(calendarId=self.calendarId,
                                         body=event).execute()
        print('Event created: %s' % (e.get('id')))

    def get_user_events_list(self, tg_username):
        now = datetime.datetime.utcnow().isoformat() + 'Z'
        events_result = self.service.events().list(
            calendarId=self.calendarId,
            timeMin=now,
            singleEvents=True,
            orderBy='startTime',
            q=f'@{str(tg_username)}'
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return False
        return events

    def get_event(self, e_id):
        return self.service.events().get(calendarId=self.calendarId, eventId=e_id).execute()

    def get_day_events(self, day):
        day_0 = day.strftime('%Y-%m-%dT%H:%M:%S+03:00')
        day_24 = (day + datetime.timedelta(hours=23, minutes=59, seconds=59)).strftime('%Y-%m-%dT%H:%M:%S+03:00')
        print(f"{day_0}\n{day_24}")
        events_result = self.service.events().list(
            calendarId=self.calendarId,
            timeMin=day_0,
            timeMax=day_24,
            singleEvents=True,
            orderBy='startTime',
        ).execute()
        events = events_result.get('items', [])
        if not events:
            return False
        return events

    def delete_event(self, e_id):
        return self.service.events().delete(calendarId=self.calendarId, eventId=e_id).execute()

    def event_edit(self, e_id, new_event):
        return self.service.events().update(calendarId=self.calendarId, eventId=e_id, body=new_event).execute()
