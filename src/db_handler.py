import sqlite3


class DatabaseHandler:
    """
    Handle interactions with the SQLite database.
    """

    def __init__(self, db_file):
        self.db_file = db_file

    def _connect(self):
        return sqlite3.connect(self.db_file)

    def initialize_table(self, table_creation_command):
        try:
            with self._connect() as conn:
                conn.execute(table_creation_command)
        except sqlite3.Error as e:
            print(f"Error initializing table: {e}")

    def register_user(self, username, user_uuid):
        """Registers a new user with a given UUID."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "INSERT INTO users (username, uuid) VALUES (?, ?)",
                    (username, user_uuid))
        except sqlite3.Error as e:
            print(f"Error registering user: {e}")

    def get_user_uuid(self, username):
        """Retrieves the UUID of a user based on their username."""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT uuid FROM users WHERE username = ?", (username,))
                result = cursor.fetchone()
                if result:
                    return result[0]
        except sqlite3.Error as e:
            print(f"Error retrieving user UUID: {e}")
        return None

    def update_public_key(self, username, public_key):
        """Updates the public key for a given user."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE users SET public_key = ? WHERE username = ?",
                    (public_key, username))
        except sqlite3.Error as e:
            print(f"Error updating public key: {e}")

    def save_aes_key_for_client(self, client_uuid, aes_key):
        """Saves the AES key for a given client."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE clients SET AESKey = ? WHERE ID = ?",
                    (aes_key, client_uuid))
        except sqlite3.Error as e:
            print(f"Error saving AES key for client: {e}")

    def get_aes_key_for_client(self, client_uuid):
        """Retrieves the AES key of a client based on their UUID."""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT AESKey FROM clients WHERE ID = ?", (client_uuid,))
                result = cursor.fetchone()
                if result:
                    return result[0]
        except sqlite3.Error as e:
            print(f"Error retrieving AES key for client: {e}")
        return None

    def update_public_key_and_aes_key(self, username, public_key, aes_key):
        """Updates the public key and AES key for a given user."""
        try:
            with self._connect() as conn:
                conn.execute(
                    "UPDATE clients SET PublicKey = ?, AESKey = ? WHERE Name = ?",
                    (public_key, aes_key, username))
        except sqlite3.Error as e:
            print(f"Error updating public key and AES key: {e}")
