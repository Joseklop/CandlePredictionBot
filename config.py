import json
import os


class Config:
    def __init__(self, config_file="config.json"):
        # Получаем путь к текущей директории
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, config_file)

        # Загружаем конфигурацию из JSON-файла
        try:
            with open(config_path, "r") as file:
                self._config = json.load(file)
        except FileNotFoundError:
            raise Exception(f"Файл конфигурации '{config_path}' не найден.")
        except json.JSONDecodeError as e:
            raise Exception(f"Ошибка чтения JSON-файла: {e}")

        # Определяем базовый путь
        self.base_dir = base_dir
        self.model_path = os.path.join(base_dir, "model/gru_model_v2.h5")
        self.websocket_path = os.path.join(base_dir, "websocketBybit.py")
        self.tg_bot_path = os.path.join(base_dir, "tg_bot.py")

    def get(self, key, default=None):
        """Возвращает значение ключа конфигурации или значение по умолчанию."""
        return self._config.get(key, default)

    def get_required(self, key):
        """Возвращает значение ключа конфигурации или вызывает исключение."""
        if key in self._config:
            return self._config[key]
        else:
            raise KeyError(f"Ключ конфигурации '{key}' не найден в config.json.")
