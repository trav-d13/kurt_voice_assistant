import Config
import os
from datetime import datetime
import pandas as pd

## System Level ##
root_path = Config.root_dir()
"""str: Path to the project root"""
data_path = '/data/voice/'
"""str: path from project root to voice data"""
DEBUG = False
"""bool: Boolean flag indicating if debug is active, in order to not write data to storage"""

## Audio Level ##
identifier = ''
"""int: Voice recording id"""
file_name = ''
"""str: File name of voice recording"""
name = ''
"""str: Name of the speaker"""
transcript = ''
"""str: Transcript of the voice recording"""
command = None
"""Enum: Type of skill executed by Kurt"""
passive_active = 'Passive'
"""str: Indicator if recording was collected through passive listening or active engagement with Kurt"""
file_path = ''
"""str: The complete file path leading to the written audio recording"""
store_name = 'audio_store.csv'
"""string: Name of csv storage of voice recording file names, transcripts and labels"""



def generate_audio_file(audio_input):
    """Method saves the recorded audio into a .wav file for training purposes.

    The audio recording is given a unique identifier corresponding to the time of creation.

    Args:
        audio_input (AudioData): The data structure containing the recorder user audio
    """
    global identifier, file_name, file_path
    if not DEBUG:
        current_time = datetime.now()  # Generate unique identifier for audion file
        identifier = current_time.strftime('%Y%m%d%H%M%S')
        file_name = identifier + '_voice' + ".wav"
        file_path = root_path + data_path + file_name

        with open(file_path, 'wb') as f:
            f.write(audio_input.get_wav_data())
        return identifier


def retrieve_transcript(query):
    """Method to retrieve the query transcript from Kurt's flow of execution

    Args:
        query (str): Speech to text result.
    """
    global transcript
    transcript = query


def retrieve_user_name(user):
    """Method to retrieve the user's name after identification in Kurt's flow of execution

    Args:
        user (str): The user's name.
    """
    global name
    name = user


def retrieve_command(skill):
    """Method to retrieve the type of skill executed by Kurt

    Args:
        skill (Enum): The type of skill executed in order to answer the user's query
    """
    global command
    command = skill


def passive_active_flag(listening_type):
    """Method to retrieve the type of listening method utilized by Kurt

    Listening is passive or active.
    Passive listening allows Kurt to learn from conversations happening in the immediate environment, but not interacting
    directly with Kurt. Whereas Active listening involves recording only when Kurt is directly queried

    Args:
        listening_type (str): String is either "Passive" or "Active" representing the listening type
    """
    global passive_active
    passive_active = listening_type


def save_audio():
    """Method performs the steps to record the information pertaining to all recorded audio files within a cvs.

    This csv offers simple conversion into a DataFrame for manipulation and use in training the voice classification model.
    """
    if not DEBUG:
        df = generate_df()  # Generate the recording DataFrame
        write_audio_store(df)  # Write the recording into


def generate_df():
    """Method generates a dataframe from the collected associated audio recording values

    Returns:
        A DataFrame representing the associated values of the audio recording
    """
    data = [[identifier, file_name, transcript, name, command, passive_active]]
    columns = ['id', 'audio_file', 'transcript', 'name', 'command', 'passive_active']
    df = pd.DataFrame(data=data, columns=columns)
    df.set_index('id', inplace=True)
    return df


def write_audio_store(df):
    """Method writes the generated df to the csv file audio_store.csv

    Args:
        df (DataFrame): Dataframe containing values of associated audio recording
    """
    store_path = root_path + data_path + store_name
    audio_store_exists = os.path.isfile(store_path)
    if audio_store_exists:
        df.to_csv(store_path, mode='a', index=True, header=False)
    else:
        df.to_csv(store_path, mode='w', index=True, header=True)

    global passive_active, command
    passive_active = 'Passive'
    command = None
