import logging
import socket
import threading
from src.config_handler import ConfigHandler
from src.db_handler import DatabaseHandler


class SecureFileServer:
    def __init__(self, port, db_handler):
        self.port = port
        self.db_handler = db_handler
        self.server_socket = None

    def _handle_client(self, client_socket):
        """
        This function handles communication with a single client.
        We'll expand on this later.
        """
        # Placeholder for handling client communications
        client_socket.close()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        logging.info(
            f"Server started on port {self.port}. Waiting for connections...")

        while True:
            client_socket, addr = self.server_socket.accept()
            print(f"Accepted connection from {addr}")
            client_thread = threading.Thread(target=self._handle_client,
                                             args=(client_socket,))
            client_thread.start()


def initialize_server():
    # Load configurations
    db_config_loader = ConfigHandler("db_config.json")
    config_data = db_config_loader.load_json()

    port_config_loader = ConfigHandler("info.port")
    port = int(port_config_loader.load_value(default_value=1357))

    # Database initialization and table creation
    db_handler = DatabaseHandler("defensive.db")
    for command in config_data.get("table_creation_commands", []):
        db_handler.initialize_table(command)

    # Initialize the server
    server = SecureFileServer(port, db_handler)

    return server


# Initializing the server (without starting it)
server_instance = initialize_server()
server_instance.start()
