import json


class ConfigHandler:
    """
    A generic configuration loader that can handle various configuration files.
    """

    def __init__(self, config_file):
        self.config_file = config_file

    def load_json(self):
        """
        Load a JSON configuration from the specified file.
        """
        try:
            with open(self.config_file, 'r') as file:
                data = json.load(file)
            return data
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            print(f"Error: {self.config_file} not found.")
            return {}

    def load_value(self, default_value=None):
        """
        Load a single value (e.g., port) from the specified file.
        Returns a default value if the file is not found.
        """
        try:
            with open(self.config_file, 'r') as file:
                value = file.readline().strip()
            return value
        except (FileNotFoundError, OSError):
            if default_value:
                return default_value
            print(f"Error: {self.config_file} not found.")
            return None

