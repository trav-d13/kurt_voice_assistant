import datetime
from time import sleep

import librosa
import numpy as np
import pandas as pd

from tensorflow import keras
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense, Dropout, Activation, Flatten
from keras.callbacks import EarlyStopping

from sklearn import preprocessing
from sklearn.model_selection import train_test_split

import Config
from src.voice.UserStore import access_user_list
from datetime import datetime

import tensorflow as tf

from silence_tensorflow import silence_tensorflow  # Remove tf hardware optimization INFO messages
silence_tensorflow()



root_path = Config.root_dir()
"""str: Path to the project root"""
model_path = '/models'
"""string: Path to model storage"""
model = Sequential()
"""Sequential: Voice classification model"""
model_name = '/model_1'
"""string: Name of stored voice classification model"""
audio_path = '/data/temp/'
"""string: Audio storage path"""
temp_audio_file = 'audio_temp.wav'
"""string: name of temporary audio file written during the classification process"""
data_path = '/data/voice/'
"""string: Path to audio data storage folder"""
user_dict = dict()
"""dict: Dictionary containing the user label, corresponding to user names as label: name pairs"""


## USER LABELS ##
# Eric -> 1
# Oscar -> 2
# Travis -> 3
# Ben -> 0
# Unknown -> 4

def initialize_model():
    generate_user_dictionary()  # Generate a dictionary of known users
    determine_retraining_requirement()
    load_model()  # Load the model from storage


def retrain_model():
    generate_user_dictionary()
    train_model()
    load_model()


def predict(audio):
    write_temp_audio_file(audio)  # Write a temporary .wav file
    audio, _ = librosa.load(root_path + audio_path + temp_audio_file)  # Load temporary audio file as librosa object
    audio_feature = feature_extraction(audio)  # generate audio feature using a mel spectrogram
    tensor_feature = tf.convert_to_tensor(audio_feature)  # Convert the feature dataframe to a tensor
    tensor_reshape = tf.reshape(tensor_feature, (1, 128))  # Reshape tensor to be accepted by the model
    prediction = model.predict(tensor_reshape, verbose=0)  # Predict the user based on the audio
    user_label = np.argmax(prediction, axis=1)  # Predict the user label
    prediction_score = prediction[0][user_label]  # Determine probability of voice being the user
    user = user_dict[user_label[0]]  # Return the user's name
    print(f"Identified user: {user} with confidence: {round(prediction_score[0] * 100, 2)}%")
    return user, prediction_score


def train_model():
    early_stop = create_model_structure()  # Create the model structure

    df = generate_raw_dataset()
    X_train, y_train, X_test, y_test = generate_final_dataset(df)

    model_history = model.fit(X_train, y_train, batch_size=20, epochs=100,
                              callbacks=[early_stop])

    score = model.evaluate(X_test, y_test, verbose=0)
    print("Model Test set Loss: ", score[0])
    print('Model Test set Accuracy: ', score[1])

    model.save(root_path + model_path + model_name)


def create_model_structure():
    global model
    model = Sequential()  # Initialize model

    model.add(Dense(128, input_shape=(128,), activation='relu'))  # First dense layer
    model.add(Dropout(0.2))

    model.add(Dense(80, activation='relu'))  # Second dense layer
    model.add(Dropout(0.5))

    model.add(Dense(40, activation='relu'))  # Third dense layer
    model.add(Dropout(0.5))

    model.add(Dense(len(user_dict), activation='softmax'))  # Output softmax layer

    model.compile(loss='categorical_crossentropy', metrics=['accuracy'], optimizer='adam')  # Model specifications
    early_stop = EarlyStopping(monitor='loss', min_delta=0, patience=100, verbose=1, mode='auto')  # Early dropout allowed
    return early_stop


def feature_extraction(x):
    mel_spec = librosa.feature.melspectrogram(y=x, sr=22050)  # Generate mel spectrogram
    mel_df = pd.DataFrame(mel_spec)  # Generate dataframe from mel_db
    feature = np.mean(mel_df.T, axis=0)  # Transpose dataframe and generate mel band mean
    return feature.to_numpy()  # Convert to numpy vector


def load_model():
    global model
    model = keras.models.load_model(root_path + model_path + model_name)  # Load the trained model


def generate_user_dictionary():
    global user_dict
    users = access_user_list()  # Access the stored user list
    user_list = users["user_list"]  # Retrieve a list of current users
    sorted_users = sorted(user_list)  # Sort the list alphabetically
    user_index = range(len(sorted_users))  # Generate a numeric index corresponding to the user label
    user_dict = dict(zip(user_index, sorted_users))  # Return a dictionary of index: name pairs


def write_temp_audio_file(audio):
    file_path = root_path + audio_path + temp_audio_file
    with open(file_path, 'wb') as f:
        f.write(audio.get_wav_data())
    sleep(1)


def generate_librosa_audio(x):
    y, sr = librosa.load(root_path + data_path + "/" + x)
    return y


def generate_raw_dataset():
    df = pd.read_csv(root_path + data_path + '/audio_store.csv')
    df['audio_librosa'] = df['audio_file'].map(generate_librosa_audio)  # Generate Librosa audio objects
    df['id'] = df['id'].apply(str)  # Convert id column to string
    return df


def generate_final_dataset(df: pd.DataFrame):
    df['feature_vector'] = df['audio_librosa'].apply(feature_extraction)
    df = df[['feature_vector', 'name']].copy()

    le = preprocessing.LabelEncoder()  # Create user numerical label
    df['label'] = pd.Series(le.fit_transform(df['name']))  # Generate user labels

    train_data, test_data = train_test_split(df, test_size=0.2)  # Train, test split
    X_train_raw = train_data['feature_vector']
    y_train_raw = train_data['label']

    X_test_raw = train_data['feature_vector']
    y_test_raw = train_data['label']

    X_train, y_train = tensor_features(X_train_raw, y_train_raw)
    X_test, y_test = tensor_features(X_test_raw, y_test_raw)
    return X_train, y_train, X_test, y_test


def tensor_features(X_data_raw, y_data_raw):
    x_expanded = pd.DataFrame(X_data_raw.tolist())  # Expand feature vector into a dataframe
    x_data = tf.convert_to_tensor(x_expanded)  # Convert dataframe to tensor

    le = preprocessing.LabelEncoder()  # Create label encoder object (One-hot-encoding)
    y_data = to_categorical(le.fit_transform(y_data_raw))  # One-hot-encode labels
    return x_data, y_data


def determine_retraining_requirement():
    df = generate_raw_dataset()
    df['date_time'] = pd.to_datetime(df['id'], format='%Y%m%d%H%M%S')
    last_date = df.tail(1)['date_time'].to_list()
    current_date = datetime.now()

    difference = current_date - last_date[0]
    if difference.days >= 1:
        print("Re-training model: \n")
        train_model()




