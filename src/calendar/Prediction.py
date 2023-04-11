# Based on https://towardsdatascience.com/forecasting-of-periodic-events-with-ml-5081db493c46
import datetime

import numpy as np
import pandas as pd

from datetime import date

from sklearn.ensemble import RandomForestClassifier
from src.calendar.Calendar import get_events_between_days, create_event, get_week


def get_history_data(event_name, service):
    """ Gets the historic data for a specific event. The data is collected from the past two months.

    Args:
        event_name: The event that we want to track back
        service: A Google calendar connection
    Returns:
        list of dates for the calendar entries, start date for the date range, end date for the date range
    """

    start = date.today() + datetime.timedelta(days=-62)
    end = date.today()
    events = get_events_between_days(service=service, start_day=start, end_day=end)
    cal_entries = []
    for event in events:
        if event_name.lower() in event['summary'].lower():
            cal_entries.append([event['start'].get('dateTime', event['start'].get('date')),
                                event['end'].get('dateTime', event['end'].get('date'))])
    return cal_entries, start, end


def most_frequent(input_list):
    """ Finds the most frequently occurring element in a list

    Args:
        input_list: a list with elements
    Returns:
        the most frequent element in the list
    """
    return max(set(input_list), key=input_list.count)


def feature_engineering(data):
    """ Adds basic feature engineering for a data frame for event forecasting.

    The method creates the following features in the input dataframe:
    month, a calendar day of the month, working day number (in a month), day of the week, week of month number,
    monthly weekday occurrence (second Wednesday of the month)

    Args:
        data: a dataframe having column 'start' for the start day of the event
    Returns:
        A dataframe with additional columns
    """
    data['mnth'] = data['start'].dt.month
    data['day'] = data['start'].dt.day
    data['workday'] = np.busday_count(data['start'].values.astype('datetime64[M]'),
                                      data['start'].values.astype('datetime64[D]'))
    data['wkday'] = data['start'].dt.weekday
    data['wk_of_mnth'] = (data['start'].dt.day - data['start'].dt.weekday - 2) // 7 + 2
    data['wkday_order'] = (data['start'].dt.day + 6) // 7  # monthly weekday occurrence
    return data


def make_hist_df(lists, start, end):
    """ Creates a historical dataframe based on lists (a list of [start, end] pairs for an event).

    Args:
        lists: a list of [start, end] pairs for an event we are trying to predict
        start: the start date for the date range we will use for the prediction
        end: the end date for the date range we will use for the prediction
    Returns:
        A dataframe of historical data for the occurrences of this event
    """
    dicts = []
    for value in lists:
        if 'T' in value[0]:  # Events during the day
            dicts.append({'start': value[0].split("T")[0], 'end': value[1].split("T")[0],
                          'start_time': value[0].split("T")[1].split("+")[0][:-3],
                          'end_time': value[1].split("T")[1].split("+")[0][:-3]})
        else:  # full day events
            dicts.append({'start': value[0], 'end': value[1],
                          'start_time': '00:00',
                          'end_time': '00:00'})

    hist_data = pd.DataFrame.from_dict(dicts)
    hist_data['event'] = 1  # the event happened on these days
    hist_data['start'] = pd.to_datetime(hist_data['start'])
    hist_data['end'] = pd.to_datetime(hist_data['end'])
    hist_data['start_time'] = hist_data['start_time']
    hist_data['end_time'] = hist_data['end_time']

    date_range = pd.date_range(start=start, end=end, name='start').to_frame(index=False)
    date_range = date_range[~date_range['start'].isin(hist_data['start'].values)]
    hist_data = pd.concat([hist_data, date_range]).reset_index().sort_values(by=['start'])
    hist_data['start_time'] = hist_data['start_time'].fillna('00:00')
    hist_data['end_time'] = hist_data['end_time'].fillna('00:00')
    hist_data['end'] = hist_data['end'].fillna(hist_data['start'], inplace=True)
    hist_data['event'] = hist_data['event'].fillna(0)
    hist_data = hist_data.drop(columns=['index'])
    hist_data = feature_engineering(hist_data)
    return hist_data


def make_predictions(hist_data, period_start, period_end):
    """ Method to make predictions for periodic data.

    The method uses a Random Forest Classifier to predict whether an event will occur in the future based on
    past data. The prediction is done with features month, a calendar day of the month, working day number (in a month),
    day of the week, week of month number and monthly weekday occurrence (second Wednesday of the month)

    Args:
        hist_data: a dataframe with historical data on the event
        period_start: a start date for the date range we will use for the prediction
        period_end: the end date for the date range we will use for the prediction
    Returns:
        A dataframe containing the information for the done prediction for the event
    """
    # use the historic data for prediction
    X_train = hist_data.drop(columns=['event', 'start', 'end', 'start_time', 'end_time'], axis=1)
    y_train = hist_data['event']

    # model for prediction
    random_forest = RandomForestClassifier(n_estimators=50, max_depth=10)
    random_forest.fit(X_train, y_train)

    # perform prediction
    date_range = pd.date_range(start=period_start, end=period_end, name='start').to_frame(index=False)
    X_test = feature_engineering(date_range)
    rf_prediction = random_forest.predict(X_test.drop(columns=['start']))

    # majority vote for start and end time based on previous month
    prev_month = hist_data.tail(30)
    prev_month = prev_month[prev_month['event'] == 1]
    starts, ends = [], []

    for _, row in X_test.iterrows():
        start_time = prev_month[prev_month['wkday'] == row['wkday']]['start_time'].mode()
        end_time = prev_month[prev_month['wkday'] == row['wkday']]['end_time'].mode()

        if len(start_time) != 0:  # most common
            starts.append(start_time[0])
        elif len(starts) != 0:  # most common based on previously chosen values
            starts.append(most_frequent(starts))
        else:
            starts.append(prev_month['start_time'].sample(n=1)[0])  # random based on previous records

        if len(end_time) != 0:  # most common
            ends.append(end_time[0])
        elif len(ends) != 0:
            ends.append(most_frequent(ends))  # most common based on previously chosen values
        else:
            ends.append(prev_month['end_time'].sample(n=1)[0])  # random based on previous records

    # create results dataframe for predictions
    new_df = X_test['start'].to_frame()
    new_df['start_time'] = starts
    new_df['end_time'] = ends
    new_df['event'] = rf_prediction
    return new_df


def create_predicted_events(service, event_name, query):
    """
    Method to create events based on past periodic data to make predictions on whether an event will happen in
    the future (week).

    The method first  predicts when the event will happen and uses the information to create the events in the
    user's Google calendar.

    Args:
        service: a Google calendar connection
        event_name: the name of the event to be predicted and scheduled
        query: the input string ('Kurt command') from which to get the prediction dates for the event (i.e. 'next week')
    Returns:
        True if the events are predicted and created, False if there is no past data to use for the predictions
    """

    event_lists, start_range, end_range = get_history_data(event_name, service)
    # does the event have historical data?
    if len(event_lists) == 0:
        return False  # no prediction can be made

    # get the historic data for the event and dates (start, end) for the remainder of the week or next week
    historic_data = make_hist_df(event_lists, start_range, end_range)
    start_day, sunday = get_week(query)

    # make predictions and schedule events
    prediction = make_predictions(hist_data=historic_data, period_start=start_day, period_end=sunday)
    for _, row in prediction.iterrows():
        if row['event'] == 1:
            day = row['start'].date()
            start_time = row['start_time']
            end_time = row['end_time']
            create_event(service, day, event_name, start_time, end_time)
    return True
