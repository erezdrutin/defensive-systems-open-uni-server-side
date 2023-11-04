import json
import os
from typing import Any, Union


class FileHandler:
    def __init__(self, filepath):
        self.filepath = filepath

    def _validate_dir(self):
        """
        Ensures that the dir path in which the file is expected to exist is
        valid. If not, attempts to create it. This will attempt to
        "recursively build the paths", in the sense that if we pass
        "X/files/file.txt", and any of the path parts is not defined (or all of
        them), then this method will create the necessary directories for
        it, meaning that both "X" and "X/files" will be created.
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
        Writes the received value to self.filepath. If the received value is
        of type bytes, we will use "wb" to write binary. Otherwise, we will
        use "w" with "utf-8" encoding.
        @param value: A value to write to self.filepath.
        @return: True if succeeded, False if not.
        """
        """
        Write a single value (e.g., port) to the specified file.
        """
        try:
            self._validate_dir()
            if isinstance(value, bytes):
                with open(self.filepath, 'wb') as file:
                    file.write(value)
            else:
                with open(self.filepath, 'w', encoding='utf-8') as file:
                    file.write(str(value))
            return True
        except OSError as e:
            print(f"Error writing to {self.filepath}: {e}")
            return False
