import re

import speech_recognition as sr
import pyttsx3
import google.cloud.texttospeech as tts
from playsound import playsound
import os

import src.voice.VoiceStorage as Store
import src.voice.UserStore as Users
import src.voice.VoiceModel as vm

from src.assistant.AssistantSkills import Skills
from src.assistant.Nlp_qa import bert_qa
from src.assistant.Teleprompt import display_script

from src.calendar.Calendar import authenticate_calendar


## System Level ##
file_path = os.path.dirname(os.path.abspath(__file__))
"""str: Path to this python script"""
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = file_path + '/credentials/key.json'  # set up client key
"""str: Set directory environment vairables to recognize the specified Google credentials"""


## Kurt Level ##
activation_word = 'hi kurt'
"""string: Activation phrase indicating that Kurt should respond to the user query"""
voice = 'en-US-News-N'
"""str: Language model of the Google's text-to-speech generator"""
engine = pyttsx3.init()
"""pyttsx3: The voice to speech engine"""
client = tts.TextToSpeechClient()
"""Google text_to_speech: The text to speech client utilized by Kurt"""


def initialize():
    """Method initializes key properties required for Kurt to function
    This method initializes the voice classification model, possibly initiating thee retraining protocol,
    depending on the last recorded voice date.
    """
    engine.setProperty('voice', 'default')  # voices[0].id for english in mac
    engine.setProperty('rate', 160)  # rate = AIs speech rate
    vm.initialize_model()


def activate():
    """Method contains the core process behind Kurt's active and passive interactions"""
    talk('Hello, I\'m Kurt')

    while True:
        query, input_audio = user_query()  # Parse user query from speech to text
        name = identify_user(input_audio)  # Identify user

        if determine_active_engagement(query):  # Perform activation word search
            active_engagement_process(query, input_audio, name)  # Active engagement
        else:  # Passive listening process
            passive_engagement_process(query, input_audio, name)


def determine_active_engagement(query):
    """Method determines if the activation phrase is contained within the query
    Args:
        query (string): The text form of the user's query
    Returns:
        A boolean value representing if the query requires active (True) or passive engagement (False)
    """
    if activation_word in query.lower():
        return True
    return False


def passive_engagement_process(query, audio, name):
    """Method contains the passive interaction process, which simply includes collecting voice samples
    Args:
        query (string): The text form of the user's query
        audio (AudioData): The audio data object of the recorded query when spoken by the user
        name (string): The user's name.
    """
    engagement_recording(query, audio, name, 'Passive')


def active_engagement_process(query, audio, name):
    """Method contains the active interaction process.
    The active interaction process is characterized by two key functionalities.
    1. The execution of skills requested by the user.
    2. The registration of a new user.
    Args:
        query (str): The text form of the user's query
        audio (AudioData): The audio data object of the recorded query when spoken by the user
        name (string): The user's name.
    """
    if new_user_query(query):  # New user query identified
        new_user_registration(query, audio)  # Begin new user registration process
    else:
        service = None  # Initialize calendar service
        if name is not None and name != 'Unknown':
            service = authenticate_calendar(name)  # Authenticate calendar service for known user
        skills_process(query, audio, name, service)  # Execute requested skill


def skills_process(query, audio, name, service):
    """ Method performs the skill execution process.
    Args:
        query (str): The text form of the user's query
        audio (AudioData): The audio data object of the recorded query when spoken by the user
        name (string): The user's name.
        service (Calendar.service): User authentication link to access calendar
    """
    query = query.lower().replace(activation_word, '')  # Remove activation word from Query
    query = query.lower().split()  # Split query into an array of strings

    if name == 'Unknown':
        active_engagement_skills(query, '', service)  # Perform skill on requested query (Unknown user)
    else:
        active_engagement_skills(query, name, service)  # Perform skill on requested query (Known user)
    engagement_recording(' '.join(query), audio, name, 'Active')  # Record observations for training purposes


def new_user_query(query):
    """Method determines if the user's query was to begin the registration process for a new user
    Note this method accomplishes this through keyword matching over the words [new, user, register, registration]
    Args:
        query (str): The text form of the user's query
    Returns:
        False if a new user query is not detected. True otherwise.
    """
    keywords = ['new', 'user', 'register', 'registration']  # Keywords
    regex_pattern = '|'.join([f'{keyword}' for keyword in keywords])  # Create regex pattern of countries
    keyword = re.search(regex_pattern, query)  # Identify country in string
    if keyword is None:  # No keywords found, not a registration query
        return False
    return True  # Is a registration query


def new_user_registration(query, audio):
    """Method performs the new user registration protocol
    The protocol is defined by three steps:
    1. Ask the user for the name (username) until one is available (not in known users)
    2. Authenticate Google calendar access with the new user. Producing a user specific token pass for future use.
    3. Perform audio collection bootstrapping process to support voice classification functionality.
    Args:
        query (str): The text form of the user's query.
        audio (AudioData): The audio data object of the recorded
                           query when spoken by the user. This will be saved for training purposes.
    """
    name = get_name()  # Gather user's name

    talk('Please give me calendar access to I can begin helping you with your schedule.')
    authenticate_calendar(name)  # New user calendar access
    Users.add_user_token(name)  # Add user-specific token to user store

    bootstrap_new_user(name, query, audio)  # Bootstrap audio samples
    vm.retrain_model()  # Retrain model to include new user in predictions


def get_name():
    """Method interacts with the user to determine their name (username).
    Note: This process is cyclical, until an acceptable name is reached by Kurt.
    Example user response: "My name is Kurt"
    Full sentence response is possible due to the use of BERT NLP QA model.
    Returns:
        The method returns the extracted user's name.
    """
    talk("What is your name?")
    name = None

    while name is None:
        user_name, input_audio = parse_command()  # Parse user query from speech to text
        answer, score = bert_qa("What is the user's name?", user_name)  # Identify name from user query using NLP model
        name = user_registration_protocol(answer, score)  # Perform registration on the given name.

    return name


def user_registration_protocol(name, score):
    """Method determines if the provided name and certain score, allows for the user to be registered under that name
    The NLP model used to extract the name from the user's query, attaches a certainty score to the extracted value.
    A low certainty score will prompt Kurt to ask for your name again.
    A high certainty score, yet an already existing user with that name will prompt you to choose another name.
    If certainty is high enough and the name is unique. You will be registered.
    Args:
        name (str): The extracted name of the new user to be registered.
        score (float): The certainty percentage of the NLP extracted name
    Returns:
        The user's name when successful registration occurs. Otherwise, None, and instructions on next steps to follow.
    """
    if score > 0.7 and not Users.ask_user_name(name):  # Successful registration
        Users.add_user(name)
        talk('Nice to meet you, your username is ' + name)
        return name
    elif score > 0.7 and Users.ask_user_name(name):  # Select alternative name
        talk("That username is already taken, please choose another")
        return None
    else:  # Uncertainty too low, no name detected
        "Please can you repeat your name, I didn't catch that."
        return None


def bootstrap_new_user(name, query, audio):
    """Method performs an audio bootstrapping for a new user in order to facilitate voice recognition functionality.
    This method generates new audio recordings (wav), and stores relevant information (label, transcript, etc) in the
    audio_store.csv file.
    Args:
        name (str): The extracted name of the new user to be registered. This will be the label of training data
        query (str): The text form of the user's registration request for saving as training data.
        audio (AudioData): The audio of the user's registration request for saving as training data.
    """
    bootstrap_samples = 5  # Number of sample recordings to collect from the user
    engagement_recording(query, audio, name, 'Bootstrap')  # Save new user registration query

    talk("For voice recognition purposes please follow the next instructions.")
    for sample in range(bootstrap_samples):
        talk("Please read out loud the displayed script")
        display_script()  # Display script
        query, audio = parse_command()  # Gather audio and text info
        engagement_recording(query, audio, name, 'Bootstrap')  # Save information
    talk('Thank you ' + name + " you are successfully registered")


def engagement_recording(query, audio, name, active_passive_flag):
    """Method saves the query, audio, username and the active/ passive flag for data recording purposes.
    Args:
        query (string): The text form of the user's query
        audio (AudioData): The audio data object of the recorded query when spoken by the user
        name (string): The user's name.
        active_passive_flag (string): Active or Passive
    """
    if len(name) != 0:  # Non-empty label
        Store.retrieve_transcript(query)  # Record transcript for storage
        Store.retrieve_user_name(name)  # Record username
        Store.passive_active_flag(active_passive_flag)  # Set engagement type flag
        Store.generate_audio_file(audio)  # Saves detected audio
        Store.save_audio()  # Save the recording


def active_engagement_skills(query, name, service):
    """Method performs skill selection and execution based on the user's query.
    Args:
        query (string): The text form of the user's query
        name (string): The username
        service (Calendar.service): User authentication link to access calendar
    """
    skills = Skills(query, service)  # Determine requested skill
    response = skills.skill_selection(name)  # Execute requested skill returning text result
    talk(response)  # Communicate response


def user_query():
    """Method asks the user how Kurt can help. The method will loop until a coherent query is determined
    Returns:
        Returns the text form of the query (query) and the recording of the user's query as input audio.
    """
    talk("How can I help you?")
    query = None
    while query is None:  # Only when query is determined, can the loop exit
        query, input_audio = parse_command()  # Parse user query from speech to text

    return query, input_audio


def identify_user(audio):
    """Method identifies the user spoke,
    The method gives a trained voice classifier the input audio to determine if Kurt recognizes the users voice.
    If the classifier predicts a user with less that 70% certainty, the uncertain user protocol is initiated.
    Args:
        audio (AudioData): Audio data from the user's query for voice classification model prediction
    Returns:
        Returns either Unknown as the name if the user is not registered. Alternatively, it returns the user's name
        when identified.
    """
    name, score = vm.predict(audio)  # Use voice classification model to predict the speaker

    if score < 0.7:  # Certainty of user prediction below 70%
        name = uncertain_user_protocol()  # Activate uncertain user protocol

    if name == "Unknown":  # User could not be detected
        talk("You are not a registered user, please go through the registration process first.")
        name = "Unknown"  # Set name to an empty string
    return name


def uncertain_user_protocol():
    """Method defines the process to follow when user identity is uncertain.
    The process includes:
    1. Ask the user for their name again.
    2. Listen to response (Response preferably full sentence) such as "my name is Kurt"
    3. If identity is unknown after 2 repetitions, then end process.
    Returns:
        The name if certainty is gained. Else if still uncertain returns None
    """
    talk("Sorry, I'm not certain who is speaking, what is your name?")
    uncertainty_tries = 0  # Current identification try
    uncertainty_try_limit = 2  # Limited number of tries to identify user

    name = None
    while name is None:  # Only when query is determined, can the loop exit
        if uncertainty_tries == uncertainty_try_limit:  # Identification tries exceeded.
            print("Uncertainty tries exceeded")
            break

        query, input_audio = parse_command()  # Parse user query from speech to text

        if query is not None:
            uncertainty_tries = uncertainty_tries + 1
            answer, score = bert_qa("What is the user's name?", query)  # Identify name from user query
            name = user_lookup(answer, score, uncertainty_tries, uncertainty_try_limit)  # Perform user lookup & response
            print("Bert answer: ", answer, " score: ", score)

    return name


def user_lookup(answer, score, uncertainty_tries, uncertainty_limit):
    """This method retrieves known users, and determined if the stated username is already registered.
    There are two events that could occur:
    1. The name is accepted and recognized as an existing user. Continuing with your query.
    2. Your name is still not recognized, prompting you to repeat your name.
    Returns:
        The method returns your name is certain of your identity. Else None is returned
    """
    if score > 0.7 and Users.ask_user_name(answer):
        talk("Thank you, I will recognize you next time")
        return answer

    if uncertainty_tries < uncertainty_limit:  # Eliminate response when used all tries
        talk("I couldn't find you. Please repeat your name.")
    return None


def talk(text: str):
    """
    This method generates a natural sounding voice for Kurt using google's text-to-speech API
    Params:
        str text: Kurt's output response in text format.
    Returns:
        A voice output as an answer to a query or indication of current process.
    """
    language_code = "-".join(voice.split("-")[:2])
    text_input = tts.SynthesisInput(text=text)  # Set the text input to be synthesized

    # Build the voice request, select the language code ("en-US") and the voice name
    voice_params = tts.VoiceSelectionParams(language_code=language_code, name=voice)

    # Select the type of audio file you want returned
    audio_config = tts.AudioConfig(audio_encoding=tts.AudioEncoding.LINEAR16)

    response = client.synthesize_speech(input=text_input, voice=voice_params, audio_config=audio_config)
    audio_file = f"{file_path}/{voice}.wav"
    with open(audio_file, "wb") as out:
        out.write(response.audio_content)
    playsound(audio_file)


def parse_command():
    """ Method identifies the activation phrase, and parses voice-to-text creating a text query for the assistant.
    This method makes use of the speech_recognition library, and will utilize the device's default microphone in
    order to detect spoken words.
    The microphone's energy threshold is dynamically adjusted based on the surrounding ambient noise.
    Returns:
        Returns a string representing the user's query in string format and the audio file of the query
    """
    listener = sr.Recognizer()  # Acts as a listener parsing voice into text
    print('Listening for  a command')

    with sr.Microphone() as source:  # connect mic
        print('Evaluating ambient noise...')
        listener.adjust_for_ambient_noise(source, duration=2)  # Adjust sensitivity based on ambient noise
        listener.dynamic_energy_threshold = True  # Allows sensitivity adjustment dynamically
        listener.pause_threshold = 3  # seconds of non-speaking audio before a phrase is considered complete
        print('Listening')
        input_audio = listener.listen(source)  # could be limited time, Google API

    try:
        print('Recognizing speech...')
        query = listener.recognize_google(input_audio, language='en-US')
        print(f'The input speech was: {query}')

    except Exception as e:  # Audio could not be transcribed
        talk('Pardon me, I did not quite catch that')
        return None, None
    return query, input_audio



