from const import DB_CONFIG
from server import Server


def main():
    server = Server.initialize_server(
        db_config=DB_CONFIG, db_file="defensive.db", port_path="port.info")
    server.start()


if __name__ == '__main__':
    main()
