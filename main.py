import logging
import subprocess
import threading

from config import Config
from logging_config import setup_logging

# Load configuration
config = Config()

# Set up logging
setup_logging("main.log")

def run_script(script_path, script_name):
    try:
        # Run the script as a separate process
        subprocess.run(["python", script_path], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running {script_name}: {e}")
    except Exception as e:
        logging.error(f"Error starting {script_name}: {e}")

def run_telegram_bot():
    run_script(config.tg_bot_path, "tg_bot.py")

def run_websocket():
    run_script(config.websocket_path, "websocketBybit.py")

if __name__ == "__main__":
    # Start the Telegram bot and WebSocket connection in separate threads
    threads = []
    threads.append(threading.Thread(target=run_telegram_bot, name="TelegramBotThread"))
    threads.append(threading.Thread(target=run_websocket, name="WebSocketThread"))

    # Start the threads
    for thread in threads:
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()
