import logging

from src.const import DB_CONFIG
from src.server import Server


def main():
    server = Server.initialize_server(
        db_config=DB_CONFIG, db_file="defensive.db", port_path="src/port.info")
    logging.warning(f'started running server on {server.port}...')
    server.start()


if __name__ == '__main__':
    main()
