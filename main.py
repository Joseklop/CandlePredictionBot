import subprocess
import threading

from config import Config

# Загрузка конфигурации
config = Config()


def run_telegram_bot():
    try:
        # Запуск tg_bot.py как отдельного процесса
        subprocess.run(["python3", config.tg_bot_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении tg_bot.py: {e}")
    except Exception as e:
        print(f"Ошибка при запуске tg_bot.py: {e}")


def run_websocket():
    try:
        # Запуск websocketBybit.py как отдельного процесса
        subprocess.run(["python3", config.websocket_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при выполнении websocketBybit.py: {e}")
    except Exception as e:
        print(f"Ошибка при запуске websocketBybit.py: {e}")


if __name__ == "__main__":
    # Запуск Telegram бота в отдельном потоке
    telegram_thread = threading.Thread(target=run_telegram_bot)
    telegram_thread.start()

    # Запуск WebSocket соединения в отдельном потоке
    websocket_thread = threading.Thread(target=run_websocket)
    websocket_thread.start()

    # Ожидание завершения работы обоих потоков
    telegram_thread.join()
    websocket_thread.join()
