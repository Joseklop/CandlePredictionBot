import logging
import os

def setup_logging(log_file="app.log"):
    # Создаем папку logs, если она не существует
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Полный путь к файлу логов
    log_path = os.path.join('logs', log_file)
    
    logger = logging.getLogger()
    
    # Проверяем наличие обработчиков, чтобы не добавлять их несколько раз
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path)
        stream_handler = logging.StreamHandler()
        
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        
        logger.setLevel(logging.INFO)
        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)
    
    return logger
