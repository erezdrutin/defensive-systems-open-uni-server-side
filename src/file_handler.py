import json
import os
from typing import Any, Union


class FileHandler:
    def __init__(self, filepath):
        self.filepath = filepath

    def _validate_dir(self):
        """
        Ensures that the directory of the specified filepath exists. If not,
        attempts to create it. This will only attempt to create the "last"
        folder in the filepath. This means that for "files/filename.txt"
        it'll create files, but for "X/files/filename.txt" it'll not create
        X, as we're only creating the "last" part of the path.
        """
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

    def load_json(self) -> Any:
        """
        Load a JSON configuration from the specified file.
        """
        try:
            with open(self.filepath, 'r') as file:
                data = json.load(file)
            return data
        except (FileNotFoundError, OSError, json.JSONDecodeError):
            print(f"Error: {self.filepath} not found.")
            return {}

    def load_value(self, default_value=None) -> Union[str, None]:
        """
        Load a single value (e.g., port) from the specified file.
        Returns a default value if the file is not found.
        """
        try:
            with open(self.filepath, 'r') as file:
                value = file.readline().strip()
            return value
        except (FileNotFoundError, OSError):
            if default_value:
                return default_value
            print(f"Error: {self.filepath} not found.")
            return None

    def write_json(self, data: Any) -> bool:
        """
        Write a JSON configuration to the specified file.
        """
        try:
            self._validate_dir()
            with open(self.filepath, 'w') as file:
                json.dump(data, file, indent=4)
            return True
        except (OSError, TypeError) as e:
            print(f"Error writing to {self.filepath}: {e}")
            return False

    def write_value(self, value: Any) -> bool:
        """
        Write a single value (e.g., port) to the specified file.
        """
        try:
            self._validate_dir()
            with open(self.filepath, 'w') as file:
                file.write(str(value))
            return True
        except OSError as e:
            print(f"Error writing to {self.filepath}: {e}")
            return False
