"""
Author: Erez Drutin
Date: 04.11.2023
Purpose: Provide DB handling functionality for the rest of the server code.
This file contains the DatabaseHandler definition, which consists of all DB
interactions between the Server and our sqlite database.
"""

import sqlite3
from typing import List, Union, Type, Dict, Any
import models
import logging


class DatabaseHandler:
    def __init__(self, db_file: str, config: Dict[str, Any],
                 logger: logging.Logger, client_tbl: str, files_tbl: str):
        """
        @param db_file: A path to the file in which the DB is stored.
        @param config: A dict that is expected to be formatted as follows:
        {
            "tbl": {
                "fetch_init": "Query to extract initial results from",
                "data_class": "Matching dataclass name to table values"
            }
        }
        """
        self.db_file = db_file
        self.config = config
        self.client_tbl = client_tbl
        self.files_tbl = files_tbl
        self.logger = logger

    def _connect(self):
        return sqlite3.connect(self.db_file)

    def table_exists(self, table_name: str) -> bool:
        query = f"SELECT count(name) FROM sqlite_master WHERE type='table' " \
                f"AND name='{table_name}'"
        # The query returns a list of tuples, where the value is expected to
        # be 1 if the table exists, 0 if not:
        try:
            return self.perform_query(query)[0][0] == 1
        except sqlite3.Error as err:
            self.logger.error(f"Failed to check if '{table_name}' exists in "
                              f"the DB or not. Exception: {err}")
            raise err

    def perform_query(self, query: str, *args, **kwargs) -> List[Any]:
        """
        Receives a query string and attempts to perform it. Returns the
        result of the execution of the query.
        @param query: A query to perform.
        @param args: Optional additional args.
        @param kwargs: Optional additional kwargs.
        @return: A list of rows, where row resembles a query result record.
        """
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(query, args or kwargs)
                return [row for row in cur.fetchall()]
        except sqlite3.Error as err:
            self.logger.warning(f"An exception was raised while performing "
                                f"the query: {query}. Exception: {err}")
            raise err

    def perform_query_to_data_model(self, query: str, data_class: Type, *args,
                                    **kwargs) -> List[Any]:
        """
        Receives a query and a dataclass to convert the query results to.
        Returns the result of the execution of the query as dataclass
        instantiated instances. We are not catching sqlite3 errors here by
        intent, so the relevant methods can handle this case.
        @param query: A query to perform.
        @param data_class: A dataclass to convert the query results to.
        @param args: Optional additional args.
        @param kwargs: Optional additional kwargs.
        @return: A list of dataclasses, where each dataclass resembles a query
        result record.
        """
        try:
            return [data_class(*row) for row in
                    self.perform_query(query, *args, **kwargs)]
        except TypeError as err:
            self.logger.error(f"Failed to convert the results of the query "
                              f"'{query}' into the dataclass: "
                              f"'{data_class.__name__}'. Exception: {err}")

    def cache_tables_data(self) -> Dict:
        """
        Expects a config dict and returns a mapping of table-datamodels lists.
        @return: A dictionary populated with tables and a list of datamodels
        that represent their values in the DB.
        """
        results = {}
        try:
            for table_name, table_info in self.config.items():
                # Fetching cached results from the tables if they exist:
                if self.table_exists(table_name):
                    results[table_name] = self.perform_query_to_data_model(
                        table_info.get("fetch_init"),
                        getattr(models, table_info.get("data_class")))
                # Creating tables & adding them, perform_query will return []:
                else:
                    results[table_name] = self.perform_query(table_info.get(
                        "create_command"))
            return results
        except sqlite3.Error:
            # Assuming no cached data from the DB in case of failure:
            return {table_name: [] for table_name in self.config.keys()}

    def get_client(self, client_name: str) -> Union[models.Client, None]:
        """
        Receives a client name and attempts to fetch it from the DB.
        Returns either a client instance or None if failed to find one.
        Letting the code "crash" in case of failure.
        @param client_name: The name of the client to fetch.
        @return: A client instantiated dataclass instance.
        """
        results = self.perform_query_to_data_model(
            query=self.config[self.client_tbl].get('get_client'),
            data_class=models.Client, name=client_name)
        return None if not len(results) else results[0]

    def add_client(self, client: models.Client) -> None:
        """
        Receives a client dataclass and attempts to add it to the DB.
        Letting the code "crash" in case of failure.
        @param client: The properties of the client to add.
        """
        self.perform_query(query=self.config[self.client_tbl].get(
            'add_client'), id=client.id, name=client.name,
            public_key=client.public_key, last_seen=client.last_seen,
            aes_key=client.aes_key)

    def add_file(self, file: models.File) -> None:
        """
        Receives a file dataclass and attempts to add it to the DB.
        Letting the code "crash" in case of failure.
        @param file: The properties of the file to add.
        """
        try:
            self.perform_query(query=self.config[self.files_tbl].get(
                'add_file'), id=file.id, file_name=file.file_name,
                path_name=file.path_name, verified=file.verified)
        except sqlite3.IntegrityError:
            self.logger.info(f"Skipping insertion, file with ID '{file.id}' "
                             f"and name '{file.file_name}' already exists.")

    def update_file_verified(self, client_id: bytes, file_name: str,
                             verified: bool = True) -> None:
        """
        Receives a client id, file name & a verified boolean value. Updates
        the verified boolean value for the client_id & file_name record(s)
        in the DB. Letting the code "crash" in case of failure.
        @param client_id: A client id to update the verified bool for.
        @param file_name: A file name to update the verified bool for.
        @param verified: A boolean to set in the DB for the received details.
        """
        self.perform_query(query=self.config[self.files_tbl].get(
            'modify_file_verified'), id=client_id, file_name=file_name,
            verified=1 if verified else 0)

    def get_aes_key_for_client(self, client_id: bytes) -> bytes:
        """
        Receives a client_id and returns its matching AES key. Letting the
        code "crash" in case of failure.
        @param client_id: A client id to fetch an AES key for.
        @return: A bytes sequence representing the requested AES key.
        """
        # Selecting the first record from the first row in the results:
        return self.perform_query(query=self.config[self.client_tbl].get(
            'get_client_aes'), id=client_id)[0][0]

    def update_public_key_and_aes_key(self, client_id: bytes, aes_key: bytes,
                                      public_key: bytes) -> None:
        """
        Receives a client_id, public key and an aes_key. Updates the public
        key and the aes key for the received client_id.
        @param client_id: A client id to update values for.
        @param aes_key: An aes key to update.
        @param public_key: A public key to update.
        """
        self.perform_query(query=self.config[self.client_tbl].get(
            'update_public_aes'), id=client_id, public_key=public_key,
            aes_key=aes_key)

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


# db_handler = DatabaseHandler('defensive.db', config=DB_CONFIG,
#                              logger=logging.getLogger("main"))
# files = db_handler.perform_query('SELECT * from files')
# clients = db_handler.perform_query('SELECT * from clients')
# print("files: ", files)
# print("clients: ", clients)
#
# print(db_handler.perform_query('SELECT ID, COUNT(*) FROM clients GROUP BY ID'))

#
#
# client = db_handler.get_client('Michael Jackson')
# db_handler.update_file_verified(client_id=client.id, file_name='cool.txt',
#                                 verified=True)
# print("files: ", db_handler.perform_query('SELECT * from files'))
