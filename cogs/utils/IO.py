from cogs.utils.logger import Logger
import os
import json

# Logger IO is handled in logger.py

settings_fail_read = "Failed to read settings"
settings_fail_write = "Failed to write settings"

c_dir = os.path.dirname(os.path.realpath(__file__))
cwd = os.path.dirname(os.path.dirname(c_dir))

settings_file_path = os.path.join(cwd, "configs", "settings.json")
# server_conf_file_path = os.path.join(cwd, "configs", "servers.json")


def fetch_from_settings(top_key: str, inner_key: str):
    """Fetch a single setting from settings.json"""
    data = read_settings_as_json()
    if data is None:
        return None
    try:
        return data[top_key][inner_key]
    except IndexError:
        return None


def read_settings_as_json():
    """Read settings json"""
    return __read_json(settings_file_path)


def write_settings(data):
    """Write settings json"""
    return __write_json(data, settings_file_path)


# def read_server_as_json():
#    """Read server settings json"""
#    return __read_json(server_conf_file_path)


# def write_server(data):
#    """Write server settings json"""
#    return __write_json(data, server_conf_file_path)


def __read_json(file_path):
    """Read the file at file_path and then return as python object
    Returns none if failed"""
    try:
        with open(file_path, "r") as f:
            r_data = f.read()
            data = json.loads(r_data)
            return data

    except Exception as e:
        Logger.write(e)
        return None


def __write_json(data, file_path):
    """Write data to the file_path file.
    Returns true if successful, False if not"""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
            return True

    except Exception as e:
        Logger.write(e)
        return False
