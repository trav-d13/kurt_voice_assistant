from datetime import datetime, timedelta, date
import os.path
import numpy as np
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

file_path = os.path.dirname(os.path.abspath(__file__))
"""str: Path to this python script"""
# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']
"""list: Contains all necessary scopes for the Google Calendar API"""
MONTHS = ["january", "february", "march", "april", "may", "june","july", "august", "september", "october", "november", "december"]
"""list: A list of months"""
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
"""list: A list of weekdays"""
DAY_EXTENSIONS = ["rd", "th", "st", "nd"]
"""list: A list of day extensions"""
CALENDAR_ID = 'primary'
"""str: Calendar ID to be used for the python scripts actions"""


def authenticate_calendar(name: str):
    """This method creates a connection to the Google Calendar API through authentication based on
    the credentials.json file (or token.json).

    The connection of the user needs authorization. This is why when the connection is made the first time the
    user will be directed to a website where they have to agree to the terms (based on listed scopes).
    Once the user has connected and agreed the terms for the first time, a local file token.json is generated that
    can be used to establish connection without having to agree to the terms again.

    Returns:
        service object that contain the user's connection to the Google Calendar API
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(f'{file_path}/credentials/token_' + name + '.json'):
        creds = Credentials.from_authorized_user_file(f'{file_path}/credentials/token_' + name + '.json', SCOPES)  # Create local token

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                f'{file_path}/credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(f'{file_path}/credentials/token_' + name + '.json', 'w') as token:
            token.write(creds.to_json())

    # Try to build connection
    service = None
    try:
        service = build('calendar', 'v3', credentials=creds)
    except HttpError as error:
        print('An error occurred: %s' % error)
    return service


def display_list_of_calendars(service):
    """Lists all the calendars available for the Google account

    Args:
        service: connection to the user's Google calendar
    """
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            print('Calendar ID:', calendar_list_entry['id'])
            print(f'In full: {calendar_list_entry}')
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break


def get_list_of_calendars(service):
    """Gives the list of all the calendars available for the Google account

    Args:
        service: connection to the user's Google calendar
    Returns:
        a list of calendar ids to be used to query calendars
    """
    calendar_ids = []
    page_token = None
    while True:
        calendar_list = service.calendarList().list(pageToken=page_token).execute()
        for calendar_list_entry in calendar_list['items']:
            calendar_ids.append(calendar_list_entry['id'])
        page_token = calendar_list.get('nextPageToken')
        if not page_token:
            break
    return calendar_ids


def get_next_events(service, n):
    """This method gets the next n events listed in the user's calendar

    Args:
        service: connection to the user's Google calendar
        n: amount of events
    Returns:
        a list of google calendar events objects
    """
    # Call the Calendar API
    now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
    print(f'Getting the upcoming {n} events')

    calendar_ids = get_list_of_calendars(service)
    events = []
    for calendar_id in calendar_ids:
        events_result = service.events().list(calendarId=calendar_id, timeMin=now,
                                              maxResults=n, singleEvents=True,
                                              orderBy='startTime').execute()
        events.extend(events_result.get('items', []))

    if not events:
        print('No upcoming events found.')

    events = sort_events(events)
    return events


def get_days_events(service, day):
    """This method gets all the scheduled events  in the user's calendar for a given day

    Args:
        service: connection to the user's Google calendar
        day (datetime.date): the specific day for the events
    Returns:
        a list of google calendar events objects
    """
    # Call the Calendar API
    if day == datetime.today().date():
        date = datetime.combine(day, datetime.now().time()).isoformat() + 'Z'  # 'Z' indicates UTC time
    else:
        date = datetime.combine(day, datetime.min.time()).isoformat() + 'Z'  # 'Z' indicates UTC time
    end_date = datetime.combine(day, datetime.max.time()).isoformat() + 'Z'  # 'Z' indicates UTC time

    print(f'Getting the upcoming events on {day}')
    calendar_ids = get_list_of_calendars(service)
    events = []
    for calendar_id in calendar_ids:
        events_result = service.events().list(calendarId=calendar_id, timeMin=date,
                                              timeMax=end_date, singleEvents=True, orderBy='startTime').execute()
        events.extend(events_result.get('items', []))

    if not events:
        print(f'No upcoming events found for {day}.')
    else:
        print(f'Found {len(events)} for {day}.')

    # Prints the start and name of the next n events
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])
    return events


def get_events_between_days(service, start_day, end_day):
    """This method gets all the scheduled events  in the user's calendar for a given day

    Args:
        service: connection to the user's Google calendar
        start_day (datetime.date): the specific starting day for the range of events
        end_day (datetime.date): the specific ending day for the range of events
    Returns:
        a list of google calendar events objects
    """
    # Call the Calendar API
    if start_day == datetime.today().date():
        start_date = datetime.combine(start_day, datetime.now().time()).isoformat() + 'Z'  # 'Z' indicates UTC time
    else:
        start_date = datetime.combine(start_day, datetime.min.time()).isoformat() + 'Z'  # 'Z' indicates UTC time
    end_date = datetime.combine(end_day, datetime.max.time()).isoformat() + 'Z'  # 'Z' indicates UTC time
    print(f'Getting the upcoming events between {start_day} and {end_day}')

    calendar_ids = get_list_of_calendars(service)
    events = []
    for calendar_id in calendar_ids:
        events_result = service.events().list(calendarId=calendar_id, timeMin=start_date,
                                              timeMax=end_date, singleEvents=True, orderBy='startTime').execute()
        events.extend(events_result.get('items', []))

    if not events:
        print(f'No events found between {start_day} and {end_day}.')
    else:
        print(f'Found {len(events)} for between {start_day} and {end_day}.')
    return events


# https://www.techwithtim.net/tutorials/voice-assistant/date-from-speech-p2/
def get_date(text):
    """This method reads a natural text and generates a specified date object based on the input strings
    content.

    Args:
        str text: string containing some date in it, can be a weekday
    Returns:
        date (datetime.date): the specific date from the text
    """
    text = text.lower()
    today = date.today()

    if text.count("today") > 0:
        return today

    if text.count("tomorrow") > 0:
        return date.today()+timedelta(days=1)

    day = -1
    day_of_week = -1
    month = -1
    year = today.year

    for word in text.split():
        if word in MONTHS:
            month = MONTHS.index(word) + 1
        elif word in DAYS:
            day_of_week = DAYS.index(word)
        elif word.isdigit() and not ('a.m' in text or 'p.m.' in text):
            day = int(word)
        else:
            for ext in DAY_EXTENSIONS:
                found = word.find(ext)
                if found > 0:
                    try:
                        day = int(word[:found])
                    except Exception as e:
                        pass

    # if the month mentioned is before the current month set the year to the next
    if month < today.month and month != -1:
        year = year+1

    # This is slightly different from the video but the correct version
    if month == -1 and day != -1:  # if we didn't find a month, but we have a day
        if day < today.day:
            month = today.month + 1
        else:
            month = today.month

    # if we only found a dta of the week
    if month == -1 and day == -1 and day_of_week != -1:
        current_day_of_week = today.weekday()
        dif = day_of_week - current_day_of_week

        if dif < 0:
            dif += 7
            if text.count("next") >= 1:
                dif += 7

        return today + timedelta(dif)

    if day != -1:
        return date(month=month, day=day, year=year)

    return today  # default


def create_event(service, date, event, start_time, end_time):
    """Creates an event to the user's Google calendar

    Args:
        service: connection to the user's Google calendar
        date (datetime.date): date for the event
        event: title for the event
        start_time: starting time for the event
        end_time: ending time for the event
    """

    # check format of input times and create datetime objects
    if type(start_time) == str:
        # datetime information
        start = start_time.split(':')
        start_date = datetime.combine(date,
                                      (datetime.min + timedelta(hours=float(start[0]), minutes=float(start[1]))).time())
    else:
        # datetime information
        start_date = datetime.combine(date, (datetime.min + timedelta(hours=start_time)).time())

    if type(end_time) == str:
        end = end_time.split(':')
        end_date = datetime.combine(date, (datetime.min + timedelta(hours=float(end[0]), minutes=float(end[1]))).time())
    else:
        end_date = datetime.combine(date, (datetime.min + timedelta(hours=end_time)).time())

    # Proper formatting
    start_date = start_date.isoformat()  # 'Z' indicates UTC time
    end_date = end_date.isoformat()  # 'Z' indicates UTC time

    # Create event
    event_result = service.events().insert(calendarId=CALENDAR_ID,
                                           body={
                                               "summary": event,
                                               "description": 'This is an event scheduled by Kurt',
                                               "start": {"dateTime": start_date, "timeZone": 'Europe/Amsterdam'},
                                               "end": {"dateTime": end_date, "timeZone": 'Europe/Amsterdam'},
                                           }).execute()
    print(f"Created an event for {date}")
    print("> summary:", event_result['summary'])
    print(f"> starts at: {start_time}")
    print(f"> ends at: {end_time}")


def contains_weekdays(text):
    """This method reads a natural text and checks whether it has a weekday, today or tomorrow in the text
        Args:
            str text: string containing natural text
    """
    for DAY in DAYS:
        if DAY in text or 'today' in text or 'tomorrow' in text or 'yesterday' in text:
            return True
    return False


def get_week(text):
    """This method reads a natural text and generates two specified date objects based on the input strings
        content, a week's starting day (monday or the current day) and the week's sunday.

        Args:
            str text: string containing some date in it, can be a weekday
        Returns:
            date (datetime.date): the specific starting date from the text for a week
            date (datetime.date): the specific ending date from the text for a week
        """
    text = text.lower()
    today = date.today()
    if text.count("this") > 0:
        weekday = today.weekday()
        return today, today + timedelta(days=(6-weekday))  # 6=sunday
    elif text.count("next") > 0:
        days_ahead = 7 - today.weekday()  # 0=monday
        return today + timedelta(days=days_ahead),  today + timedelta(days=6 + days_ahead)  # 6=sunday

    return today, today + timedelta(days=(6-today.weekday()))  # return this week by default


def sort_events(events):
    """Sorts a list of google.calendar.event items based on the date and start time

    Args:
        events:
    Returns:
        a sorted version of the list of events
    """
    # store start times as datetime
    dates = []
    for event in events:
        date = event['start'].get('dateTime', event['start'].get('date'))
        # the start date has an extra part +01:00 for UTC time, the index -6 ignores this
        dates.append(datetime.strptime(date[:-6], "%Y-%m-%dT%H:%M:%S"))
    return [events[i] for i in np.argsort(dates)]
