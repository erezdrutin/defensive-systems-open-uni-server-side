from __future__ import annotations
import logging
import socket
import threading
from typing import Dict, Any

from custom_exceptions import ClientDisconnectedError
from file_handler import FileHandler
from db_handler import DatabaseHandler

from models import ServerState
from protocol_handler import ProtocolHandler


class Server:
    def __init__(self, port: int, db_handler: DatabaseHandler,
                 state: ServerState, protocol: ProtocolHandler,
                 logger: logging.Logger):
        self.port = port
        self.db_handler = db_handler
        self.server_socket = None
        self.state: ServerState = state
        self.protocol: ProtocolHandler = protocol
        self.logger = logger

    def _handle_client(self, client_socket):
        """
        This function handles communication with a single client.
        It processes multiple requests until the client disconnects.
        """
        try:
            while True:
                # Continuously handle requests
                self.protocol.handle_request(client_socket)
        except ClientDisconnectedError as err:
            self.logger.warning(str(err))
        except (ConnectionResetError, BrokenPipeError):
            # Client disconnected unexpectedly
            self.logger.warning("Client disconnected unexpectedly.")
        except Exception as e:
            # Handle or log other exceptions
            self.logger.error(f"Error while handling client: {e}")
        finally:
            client_socket.close()
            self.logger.warning(f"Connection closed.")

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.logger.info(
            f"Server started on port {self.port}. Waiting for connections...")

        while True:
            client_socket, addr = self.server_socket.accept()
            self.logger.warning(f"Accepted connection from {addr}")
            client_thread = threading.Thread(target=self._handle_client,
                                             args=(client_socket,))
            client_thread.start()

    @staticmethod
    def init_logger(logger_name: str = "main", log_path: str = "logs.log"):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path),
                logging.StreamHandler()
            ])
        return logging.getLogger(logger_name)

    @staticmethod
    def initialize_server(db_config: Dict[str, Dict[str, Any]], db_file: str,
                          port_path: str) -> Server:
        logger = Server.init_logger()
        port_config_loader = FileHandler(port_path)
        port = int(port_config_loader.load_value(default_value=1357))

        # Database initialization and table creation
        db_handler = DatabaseHandler(db_file=db_file, config=db_config,
                                     logger=logger)

        cached_db_results = db_handler.initialize_table()
        state = ServerState(clients=cached_db_results.get('clients'),
                            files=cached_db_results.get('files'))

        protocol = ProtocolHandler(db_handler, logger)
        # Return the initialized server:
        return Server(port, db_handler, state, protocol, logger)
