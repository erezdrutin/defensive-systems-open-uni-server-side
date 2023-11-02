import sqlite3
from dataclasses import fields
from typing import List, Union, Type, Dict, Any
from src.const import CLIENTS_TABLE, FILES_TABLE, DB_CONFIG
from src.models import Client, File


class DatabaseHandler:
    """
    Handle interactions with the SQLite database.
    """

    def __init__(self, db_file: str, config: Dict[str, Any]):
        """
        @param db_file: A path to the file in which the DB is stored.
        @param config: A dict that is expected to be formatted as follows:
        {
            "tbl": {
                "fetch_init": "Query to extract initial results from",
                "data_class": "Matching dataclass to table values"
            }
        }
        """
        self.db_file = db_file
        self.config = config

    def _connect(self):
        return sqlite3.connect(self.db_file)

    def table_exists(self, table_name: str) -> bool:
        query = f"SELECT count(name) FROM sqlite_master WHERE type='table' " \
                f"AND name='{table_name}'"
        # The query returns a list of tuples, where the value is expected to
        # be 1 if the table exists, 0 if not:
        return self.perform_query(query)[0][0] == 1

    def perform_query(self, query: str, *args, **kwargs) -> List[List[Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(query, args or kwargs)
            return [row for row in cur.fetchall()]

    def perform_query_to_data_model(self, query: str, data_class: Type, *args,
                                    **kwargs) -> List[Any]:
        return [data_class(*row) for row in
                self.perform_query(query, *args, **kwargs)]

    def initialize_table(self) -> Dict:
        """
        Expects a config dict and returns a mapping of table-datamodels lists.
        @return: A dictionary populated with tables and a list of datamodels
        that represent their values in the DB.
        """
        results = {}
        for table_name, table_info in self.config.items():
            # Fetching cached results from the tables if they exist:
            if self.table_exists(table_name):
                results[table_name] = self.perform_query_to_data_model(
                    table_info.get("fetch_init"), table_info.get("data_class"))
            # Creating the tables and adding them:
            else:
                try:
                    with self._connect() as conn:
                        conn.execute(table_info.get("create_command"))
                    results[table_name] = []
                except sqlite3.Error as e:
                    print(f"Error initializing table {table_name}: {e}")
        return results

    def get_client(self, client_name: str) -> Union[Client, None]:
        results = self.perform_query_to_data_model(
            query=self.config[CLIENTS_TABLE].get('get_client'),
            data_class=Client, name=client_name)
        return None if not len(results) else results[0]

    def add_client(self, client: Client) -> None:
        self.perform_query(query=self.config[CLIENTS_TABLE].get(
            'add_client'), id=client.id, name=client.name,
            public_key=client.public_key, last_seen=client.last_seen,
            aes_key=client.aes_key)

    def add_file(self, file: File) -> None:
        self.perform_query(query=self.config[FILES_TABLE].get(
            'add_file'), id=file.id, file_name=file.file_name,
            path_name=file.path_name, verified=file.verified)

    def get_user_uuid(self, username):
        """Retrieves the UUID of a user based on their username."""
        try:
            with self._connect() as conn:
                cursor = conn.execute(
                    "SELECT uuid FROM clients WHERE username = ?", (username,))
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
                    "UPDATE clients SET public_key = ? WHERE username = ?",
                    (public_key, username))
        except sqlite3.Error as e:
            print(f"Error updating public key: {e}")

    def update_file_verified(self, client_id: bytes, file_name: str,
                             verified: bool = True):
        self.perform_query(query=self.config[FILES_TABLE].get(
            'modify_file_verified'), id=client_id, file_name=file_name,
            verified=1 if verified else 0)


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

#     def insert_data(self, table_name: str, data: dict):
#         """
#         Insert data into the specified table.
#
#         Parameters:
#             table_name (str): The name of the table to insert data into.
#             data (dict): A dictionary where keys are column names and values are the respective values to insert.
#         """
#         columns = ', '.join(data.keys())
#         placeholders = ', '.join(['?'] * len(data))
#         values = tuple(data.values())
#
#         try:
#             with self._connect() as conn:
#                 conn.execute(
#                     f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})",
#                     values)
#         except sqlite3.Error as e:
#             print(f"Error inserting data into {table_name}: {e}")
#
#
# db_handler = DatabaseHandler('./defensive.db')
#
# # Insert example clients
# clients_data = [
#     {
#         "ID": b"1234567890abcdef",
#         "Name": "Client 1",
#         "PublicKey": b"abcdef1234567890abcdef1234567890abcdef12",
#         "LastSeen": "2023-10-24 10:00:00",
#         "AESKey": b"abcdef1234567890"
#     },
#     {
#         "ID": b"abcdef1234567890",
#         "Name": "Client 2",
#         "PublicKey": b"1234567890abcdef1234567890abcdef12345678",
#         "LastSeen": "2023-10-24 11:00:00",
#         "AESKey": b"1234567890abcdef"
#     }
# ]
#
# for client in clients_data:
#     db_handler.insert_data("clients", client)
#
# # Insert example files
# files_data = [
#     {
#         "ID": b"1234567890abcdef",
#         "FileName": "file1.txt",
#         "PathName": "/path/to/file1.txt",
#         "Verified": True
#     },
#     {
#         "ID": b"abcdef1234567890",
#         "FileName": "file2.txt",
#         "PathName": "/path/to/file2.txt",
#         "Verified": False
#     }
# ]
#
# for file in files_data:
#     db_handler.insert_data("files", file)


# db_handler = DatabaseHandler('../defensive.db', config=DB_CONFIG)
# files = db_handler.perform_query('SELECT * from files')
# clients = db_handler.perform_query('SELECT * from clients')
# print("files: ", files)
# print("clients: ", clients)
#
#
# client = db_handler.get_client('Michael Jackson')
# db_handler.update_file_verified(client_id=client.id, file_name='cool.txt',
#                                 verified=True)
# print("files: ", db_handler.perform_query('SELECT * from files'))
