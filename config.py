import json
import os


class Config:
    def __init__(self, config_file="config.json"):
        """
        Initialize the Config class by loading the configuration from a JSON file.

        Args:
            config_file (str): The name of the configuration file.

        Raises:
            Exception: If the configuration file is not found or if there is an error reading the JSON file.
        """
        # Get the path to the current directory
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_file)

        # Load the configuration from the JSON file
        try:
            with open(config_path, "r") as file:
                self._config = json.load(file)
        except FileNotFoundError:
            raise Exception(f"Configuration file '{config_path}' not found.")
        except json.JSONDecodeError as e:
            raise Exception(f"Error reading JSON file: {e}")

        # Define base path and other paths
        self.base_dir = base_dir
        self.model_path = os.path.join(base_dir, "model", "gru_model_v2.h5")
        self.websocket_path = os.path.join(base_dir, "websocketBybit.py")
        self.tg_bot_path = os.path.join(base_dir, "tg_bot.py")

    def get(self, key, default=None):
        """
        Get the value of a configuration key or return the default value.

        Args:
            key (str): The key to look up in the configuration.
            default: The default value to return if the key is not found.

        Returns:
            The value of the configuration key or the default value.
        """
        return self._config.get(key, default)
