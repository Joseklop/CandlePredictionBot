# Используем официальный образ Python 3.11-slim
FROM python:3.11-slim

# Устанавливаем зависимости для компиляции и установки пакетов
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    python3-openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Poetry
RUN pip install poetry

# Обновляем переменную окружения PATH для использования Poetry
ENV PATH="/root/.local/bin:$PATH"

# Создаем рабочую директорию
WORKDIR /app

# Копируем pyproject.toml и poetry.lock в контейнер
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости проекта
RUN poetry config virtualenvs.create false
RUN poetry install

# Копируем остальные файлы проекта
COPY . /app/

# Указываем команду для запуска бота
CMD ["poetry", "run", "python", "tg_bot.py"]
