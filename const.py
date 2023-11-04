from enum import Enum


SERVER_VERSION = '3'


class RequestCodes(Enum):
    REGISTRATION = 1025
    SEND_PUBLIC_KEY = 1026
    RECONNECT = 1027
    SEND_FILE = 1028
    CRC_CORRECT = 1029
    CRC_INCORRECT_RESEND = 1030
    CRC_INCORRECT_DONE = 1031


class ResponseCodes(Enum):
    REGISTRATION_SUCCESS = 2100
    REGISTRATION_FAILED = 2101
    RECEIVED_PUBLIC_KEY_SEND_AES = 2102
    FILE_RECEIVED_CRC_OK = 2103
    CONFIRM_MSG = 2104
    APPROVE_RECONNECT_SEND_AES = 2105
    RECONNECT_REJECTED = 2106
    GENERAL_ERROR = 2107


CLIENTS_TABLE = "clients"
FILES_TABLE = "files"
CLIENT_ID_SIZE = 16
CLIENTS_NAME_SIZE = 255
CLIENTS_PUB_KEY_SIZE = 160
CLIENTS_AES_KEY_SIZE = 16

DB_CONFIG = {
    CLIENTS_TABLE: {
        "create_command": f"CREATE TABLE IF NOT EXISTS {CLIENTS_TABLE} (ID BLOB({CLIENT_ID_SIZE}) PRIMARY KEY, name TEXT({CLIENTS_NAME_SIZE}) NOT NULL, PublicKey BLOB({CLIENTS_PUB_KEY_SIZE}) NULL, LastSeen DATETIME NOT NULL, AESKey BLOB({CLIENTS_AES_KEY_SIZE}) NULL)",
        # :id is a parameter for this query:
        "get_client": f"SELECT * FROM {CLIENTS_TABLE} WHERE name=:name",
        "add_client": f"INSERT INTO {CLIENTS_TABLE} (ID, name, PublicKey, LastSeen, AESKey) VALUES (:id, :name, :public_key, :last_seen, :aes_key)",
        "fetch_init": f"SELECT * FROM {CLIENTS_TABLE}",
        "get_client_aes": f"SELECT AESKey FROM {CLIENTS_TABLE} WHERE ID=:id",
        "update_public_aes": f"UPDATE {CLIENTS_TABLE} SET PublicKey=:public_key, AESKey=:aes_key WHERE ID=:id",
        "data_class": "Client"
    },
    FILES_TABLE: {
        "create_command": f"CREATE TABLE IF NOT EXISTS {FILES_TABLE} (ID BLOB({CLIENT_ID_SIZE}) NOT NULL, Filename TEXT(255) NOT NULL, Pathname TEXT(255) NOT NULL, Verified BOOLEAN NOT NULL, FOREIGN KEY(ID) REFERENCES clients(ID), UNIQUE(ID, Filename))",
        "fetch_init": f"SELECT * FROM {FILES_TABLE}",
        "add_file": f"INSERT INTO {FILES_TABLE} (ID, Filename, Pathname, Verified) VALUES (:id, :file_name, :path_name, :verified)",
        "modify_file_verified": f"UPDATE {FILES_TABLE} SET Verified=:verified WHERE ID=:id AND FileName=:file_name",
        "data_class": "File"
    }
}

FILES_STORAGE_FOLDER = "./storage"
