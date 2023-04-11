import sys
from datetime import datetime
import webbrowser
from enum import Enum
import wikipedia
import pyjokes
import src.voice.VoiceStorage as vc
import src.calendar.Calendar as calendar
import src.calendar.Prediction as predict


class Command(Enum):
    """Class serving as Command types, and associated keywords"""
    SAY = ['say', 'greet', 'repeat']
    SEARCH = ['search', 'look up', 'google']
    TIME = ['time', 'what time is it', 'what is the time', 'can you tell me the time', 'tell me the time']
    WIKIPEDIA = ['wikipedia', 'summarize']
    JOKE = ['joke', 'can you tell me a joke', 'tell me something funny', 'something funny']
    READ_SCHEDULE = ['what do i have', 'do i have plans', 'am i busy', 'read my', 'read schedule']
    SCHEDULE_EVENT = ['book', 'schedule', 'create']
    EXIT = ['quit', 'exit', 'leave', 'finish', 'end', 'close', 'goodbye', 'good night']
    PREDICT = ['predict']
    UNKNOWN = ''


# REFERENCE: https://github.com/Mikael-Codes/ai-assistant
class Skills:
    """This class serves as a store of all assistant skills that can be performed.

    Skill selection is based off of the passed query which informs skill selection, the skill's
    subsequent execution, and a response in a format the assistant can utilize

    Args:
        str query: A query asked by the users to the personal assistant.
        calendar_service: A connection to the user's Google calendar
    """

    def __init__(self, query, calendar_service):
        self.query = query
        self.calendar_service = calendar_service

    def skill_selection(self, name):
        """Method selects a skill to be executed based off of query keyword.

        This skill is retrieved and stored in order to gather labelled training data.

        Returns:
            A string formatted response that will be transformed by text-to-speech as the assistant's response.
            If no skill is selected, a default response will be returned.
        """

        keyword = self.check_verbal_options()

        if keyword is None:
            keyword = self.query.pop(0)

        match keyword:
            case 'say':
                vc.retrieve_command(Command.SAY.name)
                return self.greet_repeat(name)
            case 'search':
                vc.retrieve_command(Command.SEARCH.name)
                return self.web_search()
            case 'time':
                vc.retrieve_command(Command.TIME.name)
                return self.get_time(name)
            case 'wikipedia':
                vc.retrieve_command(Command.WIKIPEDIA.name)
                return self.wikipedia_summary()
            case 'joke':
                vc.retrieve_command(Command.JOKE.name)
                return self.tell_joke(name)
            case 'read schedule':
                vc.retrieve_command(Command.READ_SCHEDULE.name)
                text = ' '.join(self.query)
                if 'week' in text and not calendar.contains_weekdays(text):
                    start, end = calendar.get_week(text)
                    return self.read_weeks_schedule(start, end)
                day = calendar.get_date(text)
                return self.read_days_schedule(day)
            case 'schedule event':
                vc.retrieve_command(Command.SCHEDULE_EVENT.name)
                return self.create_event()
            case 'predict':
                vc.retrieve_command(Command.PREDICT.name)
                return self.predict_event(name)
            case 'quit':
                vc.retrieve_command(Command.EXIT.name)
                return "goodbye", self.quit()
            case _:
                vc.retrieve_command(Command.UNKNOWN.name)
                return 'Sorry I do not possess that skill at this time'

    def check_verbal_options(self):
        """ Function that checks what was said by the user in different variations
            Returns: the keyword command extracted from the user's sentence
        """
        for phrase in Command.READ_SCHEDULE.value:
            if phrase in ' '.join(self.query):
                return 'read schedule'
        for phrase in Command.SCHEDULE_EVENT.value:
            if phrase in ' '.join(self.query):
                return 'schedule event'
        for phrase in Command.TIME.value:
            if phrase in ' '.join(self.query):
                return 'time'
        for phrase in Command.JOKE.value:
            if phrase in ' '.join(self.query):
                return 'joke'
        for phrase in Command.EXIT.value:
            if phrase in ' '.join(self.query):
                return 'quit'
        for phrase in Command.SEARCH.value:
            if phrase in ' '.join(self.query):
                return 'search'
        for phrase in Command.PREDICT.value:
            if phrase in ' '.join(self.query):
                return 'predict'

        return None

    def greet_repeat(self, user_id='you'):
        """Method is two-fold skill either greeting the users or repeating what they have said.

        Args:
            str user_id: This parameter serves to personalize the greeting of a recognized users.

        Returns:
            A string either returning a greeting or repeating what the users spoke.
        """
        if 'hello' in self.query:
            return 'hello' + user_id
        else:
            self.query.pop(0)
            speech = ' '.join(self.query)
            return speech

    def web_search(self):
        """This method performs a web search based on the users query to the assistant.

        This method will open a new Google search response on your default browser.

        Returns:
            This method will open a new Google search page on the queried topic, and will return a string which will
            serve as a response to the users indicating a search is in progress.
        """
        base_url = "http://www.google.com/search?q="
        speech = ' '.join(self.query)
        webbrowser.open_new(base_url + speech)
        return f'Searching for {speech}'

    def get_time(self, name):
        """This method will access the current time as a skill.

        Returns:
            This method will return a string indicating the current time.
        """
        now = datetime.now().strftime('%I:%M %p')
        return name + f' the current time is {now}'

    def wikipedia_summary(self):
        """This method performs a wikipedia search on the user's query as a skill.

        Returns:
            Returns a string contained a summary of the searched wikipedia page.

        Raises:
            DisambiguationError: This error is raises and accepts disambiguation error (ambitious article title)
            returning a random page summary from the available pages.
        """
        search_subject = ' '.join(self.query)
        search_results = wikipedia.search(search_subject)
        if not search_results:
            return 'No result received'
        try:
            wiki_page = wikipedia.page(search_results[0], auto_suggest=False)
        except wikipedia.DisambiguationError as error:
            wiki_page = wikipedia.page(error.options[0])

        print(wiki_page.title)
        wiki_summary = str(wiki_page.summary)
        return wiki_summary

    def tell_joke(self, name):
        """This method is a skill that tells the users a joke.

        Returns:
            A string formatted joke
        """
        return name + " I have a joke for you.. " + pyjokes.get_joke()

    def read_days_schedule(self, day):
        """This method is a skill that reads the user's events of the day

        Args:
             day: a date for the events
        Returns:
            str response: a string listing all the events on the day
        """
        if self.calendar_service is None:  # Catch for unknown user
            return f'As an Unknown user, I don\'t have access to your calendar. Please register first'

        events = calendar.get_days_events(self.calendar_service, day)
        if not events:
            return 'No upcoming events found for this day.'
        else:
            response = f"You have {len(events)} events on this day."
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                start_time = str(start.split("T")[1].split("+")[0][:-3])  # get the hour the event starts
                if int(start_time.split(":")[0]) < 12:  # if the event is in the morning
                    start_time = start_time + "am"
                else:
                    start_time = str(int(start_time.split(":")[0]) - 12)  # convert 24 hour time to regular
                    start_time = start_time + "pm"
                response += " " + event["summary"] + " at " + start_time + "."
            return response

    def read_weeks_schedule(self, start, end):
        """This method is a skill that reads the user's events of the day

        Args:
             start: a date for the start of the week
             end: a date for the end of the week
        Returns:
            str response: a string listing all the events on that week
        """

        if self.calendar_service is None:  # Catch for unknown user
            return f'As an Unknown user, I don\'t have access to your calendar. Please register first'

        events = calendar.get_events_between_days(self.calendar_service, start, end)
        if not events:
            return 'No upcoming events found for the week.'
        else:
            response = f"You have {len(events)} events on that week."
            prev_day = start.weekday()
            response += f"On {calendar.DAYS[prev_day]}"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                day = datetime.strptime(start[:-6], "%Y-%m-%dT%H:%M:%S").weekday()
                start_time = str(start.split("T")[1].split("+")[0][:-3])  # get the hour the event starts
                if int(start_time.split(":")[0]) < 12:  # if the event is in the morning
                    start_time = start_time + "am"
                else:
                    start_time = str(int(start_time.split(":")[0]) - 12)  # convert 24 hour time to regular
                    start_time = start_time + "pm"

                if prev_day != day:
                    prev_day = day
                    response += f"On {calendar.DAYS[day]}"
                response += " " + event["summary"] + " " + " at " + start_time + "."
            return response

    def create_event(self):
        """This method is a skill that creates an event in the user's account calendar
        """
        if self.calendar_service is None:  # Catch for unknown user
            return f'As an Unknown user, I don\'t have access to your calendar. Please register first'

        day = calendar.get_date(' '.join(self.query))
        event = self.query[1]
        try:
            start_temp = self.query[self.query.index('from') + 1].split(':')
            start_time = float(start_temp[0])
            end_temp = self.query[self.query.index('to') + 1].split(':')
            end_time = float(end_temp[0])
        except ValueError:
            return 'Failed to schedule the event.'

        if self.query[self.query.index('from') + 2] != 'a.m.':
            start_time += 12
        if self.query[self.query.index('to') + 2] != 'a.m.':
            end_time += 12

        # handle minutes in the start/end times
        if len(start_temp) > 1:
            start_time = f'{int(start_time)}:{start_temp[1]}'
        if len(end_temp) > 1:
            end_time = f'{int(end_time)}:{end_temp[1]}'

        calendar.create_event(self.calendar_service, day, event, start_time, end_time)
        return f'The event is now in your schedule.'

    def predict_event(self, name):
        """This method indicates a calendar prediction is required to be performed based on the learned user calendar.

        Returns: A vocal response indicating a successful prediction, or alternatively is there is not sufficient data to
        perform the prediction, a notification that this is the case.
        """
        if self.calendar_service is None:  # Catch for unknown user
            return f'As an Unknown user, I don\'t have access to your calendar. Please register first'

        event_name_ind = self.query.index('predict') + 1  # Command must follow the form "Hi Kurt, predict ..(event_name).. for ..(time_frame)..
        prediction_flag = predict.create_predicted_events(self.calendar_service, self.query[event_name_ind], ' '.join(self.query))

        if prediction_flag:
            return f'The event has been scheduled for you {name}'
        else:
            return f'Unfortunately there is not enough available data to make that prediction {name}'

    def quit(self):
        """This method will disable and exit the assistant program"""
        sys.exit()
