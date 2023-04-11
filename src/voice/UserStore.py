import Config
import json

root_path = Config.root_dir()
"""str: Path to the project root"""
data_path = '/data/users'
"""str: path from project root to voice data"""
file_name = '/user_list.txt'
"""str: The complete file path leading to user_list file. This contains all user information"""


def ask_user_name(name):
    """Method queries the user_list file store if a user with the passed name exists.

    If the queried user does not exist, a new user is added to the user store.

    Returns:
        A boolean value, True if the user exists and False if the user didn't exist.
    """
    users = access_user_list()
    user_list = users["user_list"]
    if name in user_list:  # Name detected in user list
        return True

    return False


def add_user(name):
    """Method adds a new user to the registered users list

    Args:
        name (str): Name of the new user to be registered
    """
    users = access_user_list()  # Access user information
    user_list = users["user_list"]  # Generate a username list

    user_list.append(name)  # Add new username to the list
    users["user_list"] = user_list  # Update user_list with new username
    write_user_list(users)  # Store user information


def add_user_token(name: str):
    """Method saves new user Calendar access token

    Access token file name is saved as "token_Name.json
    The token list, records all saved token file names for later access.

    Args:
        name (str): The name of the user, whose access token it being saved.
    """
    users = access_user_list()
    user_tokens = users["user_tokens"]

    user_tokens.append("token_" + name + ".json")
    users["user_tokens"] = user_tokens
    write_user_list(users)


def access_user_list():
    """Method to access the user_list.txt file, reading it in as a dictionary"""
    with open(root_path + data_path + file_name) as f:
        data = f.read()
        return json.loads(data)


def write_user_list(users):
    """Method to write an updated user_list dictionary to the storage file.

    Args:
        users (dict): A dictionary containing a record of all registered users
    """
    with open(root_path + data_path + file_name, 'w') as f:
        f.write(json.dumps(users))
