from src.config_handler import ConfigHandler
from src.db_handler import DatabaseHandler


def main():
    # Example usage for loading a JSON configuration:
    db_config_loader = ConfigHandler("src/db_config.json")
    config_data = db_config_loader.load_json()

    # Example usage for loading a single value (e.g., port):
    port_config_loader = ConfigHandler("info.port")
    port = port_config_loader.load_value(default_value=1357)

    # Database initialization and table creation
    db_handler = DatabaseHandler("defensive.db")
    for command in config_data["table_creation_commands"]:
        db_handler.initialize_table(command)


if __name__ == '__main__':
    main()
